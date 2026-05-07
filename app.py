from apscheduler.schedulers.background import BackgroundScheduler
import atexit
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
load_dotenv()
import os
import sqlite3
import psycopg2
from psycopg2.extras import RealDictCursor
import threading
import requests
import time
from datetime import datetime
from flask import Flask, request, make_response, render_template, redirect
import africastalking

app = Flask(__name__)

# ==========================================
# SECURITY VAULT 
# ==========================================
app.secret_key = 'super_secret_project_key_change_later' # Required for secure sessions

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login' # If someone tries to bypass, redirect them here

# Create the Admin User Class
class AdminUser(UserMixin):
    def __init__(self, id, username, role, province):
        self.id = id
        self.username = username
        self.role = role
        self.province = province

@login_manager.user_loader
def load_user(user_id):
    conn = get_db_connection()
    admin = conn.execute('SELECT * FROM admins WHERE id = ?', (user_id,)).fetchone()
    conn.close()
    if admin:
        return AdminUser(admin['id'], admin['username'], admin['role'], admin['province'])
    return None

# --- Configuration & Environment Variables ---
AT_USERNAME = os.getenv("AT_USERNAME", "sandbox") 
AT_API_KEY = os.getenv("AT_API_KEY", "your_africastalking_api_key")
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY", "your_openweather_key")

africastalking.initialize(AT_USERNAME, AT_API_KEY)
sms = africastalking.SMS

DB_PATH = 'maize_connect.db'

# --- The National Location Map ---
LOCATIONS = {
    '1': ('Harare', 'Harare'),
    '2': ('Bulawayo', 'Bulawayo'),
    '3': ('Mutare', 'Manicaland'),
    '4': ('Gweru', 'Midlands'),
    '5': ('Masvingo', 'Masvingo'),
    '6': ('Chinhoyi', 'Mashonaland West'),
    '7': ('Bindura', 'Mashonaland Central'),
    '8': ('Marondera', 'Mashonaland East'),
    '9': ('Gwanda', 'Matabeleland South'),
    '10': ('Lupane', 'Matabeleland North')
}

# ==========================================
# DUAL-ENGINE DATABASE WRAPPER
# ==========================================
class DBWrapper:
    def __init__(self):
        self.db_url = os.getenv("DATABASE_URL")
        if self.db_url:
            # If on Render, use PostgreSQL
            self.conn = psycopg2.connect(self.db_url, cursor_factory=RealDictCursor)
            self.is_pg = True
        else:
            # If on local computer, use SQLite (kept your thread safety setting)
            self.conn = sqlite3.connect(DB_PATH, check_same_thread=False)
            self.conn.row_factory = sqlite3.Row
            self.is_pg = False

    def execute(self, query, params=()):
        if self.is_pg:
            # Automatically translates SQLite '?' into PostgreSQL '%s'
            query = query.replace('?', '%s')
            cursor = self.conn.cursor()
            cursor.execute(query, params)
            return cursor
        else:
            return self.conn.execute(query, params)

    def commit(self):
        self.conn.commit()

    def close(self):
        self.conn.close()

def get_db_connection():
    return DBWrapper()

# --- Database Helper Functions ---
def get_user(phone_number):
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE phone_number = ?', (phone_number,)).fetchone()
    conn.close()
    return user

def create_user(phone_number, full_name, pin, province, town, sec_question, sec_answer):
    conn = get_db_connection()
    conn.execute('''
        INSERT INTO users (phone_number, full_name, pin, province, town, security_question, security_answer) 
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (phone_number, full_name, pin, province, town, sec_question, sec_answer.lower().strip()))
    conn.commit()
    conn.close()

# --- Automated Weather Sync Task (UPGRADED DYNAMIC YEAR) ---
def fetch_national_weather():
    """Fetches both 3-day live forecast AND statistical December outlook dynamically for the current year."""
    print(f"[{datetime.now()}] Starting Dual API Weather Sync...")
    
    VISUAL_CROSSING_KEY = os.getenv("VISUAL_CROSSING_KEY")
    if not VISUAL_CROSSING_KEY:
        print("WARNING: Missing Visual Crossing API Key in .env")
        return

    conn = get_db_connection()
    
    # DYNAMIC TIME: Automatically get the current year (e.g., 2026, 2027, 2030)
    current_year = datetime.now().year
    short_year = str(current_year)[-2:] # Gets '26' or '27' for the SMS text
    
    for key, (city_name, prov_name) in LOCATIONS.items():
        # 1. Fetch Short-Term (Live API)
        short_url = f"https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/{city_name},ZW?unitGroup=metric&key={VISUAL_CROSSING_KEY}"
        
        # 2. Fetch Long-Term (Dynamic December API)
        # It automatically injects the current year into the URL!
        long_url = f"https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/{city_name},ZW/{current_year}-12-01/{current_year}-12-31?unitGroup=metric&key={VISUAL_CROSSING_KEY}"
        
        try:
            # --- Process Live 3-Day Forecast ---
            short_resp = requests.get(short_url, timeout=10)
            if short_resp.status_code == 200:
                short_data = short_resp.json()
                today = short_data['days'][0]
                tmrw = short_data['days'][1]
                day3 = short_data['days'][2]
                
                forecast_text = (
                    f"3-Day: Today {today['conditions']} {round(today['tempmax'])}C. "
                    f"Tmrw {tmrw['conditions']} {round(tmrw['tempmax'])}C. "
                    f"Next {day3['conditions']} {round(day3['tempmax'])}C. "
                    f"Rain Prob: {today['precipprob']}%."
                )
            else:
                forecast_text = "3-Day: API Error. Using Fallback."

            # --- Process Dynamic December Outlook ---
            long_resp = requests.get(long_url, timeout=15)
            if long_resp.status_code == 200:
                long_data = long_resp.json()
                
                total_rain = sum(day.get('precip', 0) for day in long_data['days'] if day.get('precip'))
                avg_temp = sum(day.get('temp', 0) for day in long_data['days'] if day.get('temp')) / len(long_data['days'])
                
                if total_rain > 150:
                    advice = "Heavy rains expected. High-yield maize ideal."
                elif total_rain > 80:
                    advice = "Normal rains expected. Good for standard maize."
                else:
                    advice = "Low rainfall expected. Drought-resistant crops advised."
                    
                # Dynamically changes the SMS text to say "Dec '26" or "Dec '27"
                outlook_text = f"Dec '{short_year} API Est: ~{round(total_rain)}mm rain, {round(avg_temp)}C Avg. {advice}"
            else:
                outlook_text = f"Dec '{short_year} API Est: Normal seasonal rains expected (Fallback)."

            print(f"Live API Data & Dec '{short_year} Outlook fetched for {city_name}.")

        except Exception as e:
            print(f"Network Failure for {city_name}. Using Fallback Data.")
            forecast_text = "3-Day: Network Error. Using Fallback."
            outlook_text = f"Dec '{short_year} API Est: Normal seasonal rains expected (Fallback)."
            
        conn.execute('''
            INSERT INTO weather (province, town, forecast, outlook) 
            VALUES (?, ?, ?, ?) 
            ON CONFLICT(province) DO UPDATE SET 
            town=excluded.town,
            forecast=excluded.forecast, 
            outlook=excluded.outlook,
            date_updated=CURRENT_TIMESTAMP
        ''', (prov_name, city_name, forecast_text, outlook_text))
        
        time.sleep(1) 
            
    conn.commit()
    conn.close()
    print(f"Dual Weather Sync Complete for {current_year}.")

# --- Asynchronous SMS Task ---
def send_sms_async(phone_number, service_choice):
    """Fetches data from DB based on user's province and sends detailed SMS."""
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE phone_number = ?', (phone_number,)).fetchone()
    
    if not user:
        conn.close()
        return

    user_province = user['province']
    message = f"MaizeConnect ({user_province}):\n"
    
    if service_choice == '1':
        data = conn.execute('SELECT * FROM market_prices WHERE province = ?', (user_province,)).fetchall()
        if data:
            message += "Markets:\n"
            for row in data:
                message += f"- {row['market_name']} ({row['town']}): ${row['price_per_ton']}/Ton\n"
        else:
            message += "No price data available for your region today."

    elif service_choice == '2':
        data = conn.execute('SELECT * FROM weather WHERE province = ? LIMIT 1', (user_province,)).fetchone()
        if data:
            # UPGRADE: Pull both the live forecast and the API-generated outlook directly from the DB
            message += f"{data['forecast']}\n{data['outlook']}"
        else:
            message += "Weather data currently syncing. Please wait 1 minute."

    elif service_choice == '3':
        data = conn.execute('SELECT * FROM inputs WHERE province = ?', (user_province,)).fetchall()
        if data:
            message += "Inputs:\n"
            for row in data:
                message += f"- {row['supplier_name']} ({row['town']}): {row['item_name']} @ ${row['price']}\n"
        else:
             message += "No input data available for your region today."
    
    conn.close()
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = sms.send(message, [phone_number])
            print(f"SMS queued to {phone_number} on attempt {attempt + 1}: {response}")
            break 
        except Exception as e:
            print(f"SMS attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(2) 
            else:
                print(f"CRITICAL: Failed to send SMS to {phone_number} after 3 attempts.")

# ==========================================
# SECURE AUTHENTICATION ROUTES
# ==========================================

# ==========================================
# ROOT REDIRECT
# ==========================================
@app.route('/')
def home():
    return redirect('/login')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        conn = get_db_connection()
        admin = conn.execute('SELECT * FROM admins WHERE username = ?', (username,)).fetchone()
        conn.close()
        
        if admin and check_password_hash(admin['password_hash'], password):
            # --- NEW UPGRADE: AGENT STATUS NOTIFICATIONS ---
            if admin['status'] == 'pending':
                return render_template('login.html', view='login', error="Status: Pending Approval. Please wait for the Main Admin to approve your account.")
                
            elif admin['status'] == 'revoked':
                return render_template('login.html', view='login', error="Access Denied: Your agent privileges have been revoked by the Main Admin.")
                
            elif admin['status'] == 'rejected':
                return render_template('login.html', view='login', error="Access Denied: Your agent registration application was rejected.")
            # -----------------------------------------------
            
            # If status is 'approved' (or they are the master admin), log them in
            user = AdminUser(admin['id'], admin['username'], admin['role'], admin['province'])
            login_user(user)
            return redirect('/dashboard')
        else:
            return render_template('login.html', view='login', error="Invalid credentials. Intrusion logged.")
            
    return render_template('login.html', view='login')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/login')

@app.route('/register_admin', methods=['GET', 'POST'])
def register_admin():
    if request.method == 'POST':
        conn = get_db_connection()
        
        # FIX 1: Safely count agents using a labeled column 'total' for both databases
        count_row = conn.execute("SELECT COUNT(*) as total FROM admins WHERE role = 'agent' AND status = 'approved'").fetchone()
        agent_count = count_row['total']
        
        if agent_count >= 10:
            conn.close()
            return render_template('login.html', view='register', error="System Full: Maximum of 10 Regional Agents reached.")

        username = request.form.get('username')
        password = request.form.get('password')
        province = request.form.get('province')
        question = request.form.get('security_question')
        answer = request.form.get('security_answer')
        
        # --- NEW UPGRADE: ONE AGENT PER PROVINCE CHECK ---
        # Checks if anyone (pending or approved) is already assigned to this province
        prov_check = conn.execute("SELECT COUNT(*) as total FROM admins WHERE role = 'agent' AND province = ?", (province,)).fetchone()
        
        if prov_check['total'] > 0:
            conn.close()
            return render_template('login.html', view='register', error=f"Province Taken: An agent is already registered or pending for {province}.")
        # -------------------------------------------------
        
        password_hash = generate_password_hash(password)
        answer_hash = generate_password_hash(answer.lower().strip()) 
        
        try:
            # NEW AGENTS ARE INSERTED AS 'pending'
            conn.execute('''
                INSERT INTO admins (username, password_hash, province, security_question, security_answer_hash, role, status) 
                VALUES (?, ?, ?, ?, ?, 'agent', 'pending')
            ''', (username, password_hash, province, question, answer_hash))
            conn.commit()
            msg = "Request sent! Please wait for the Main Admin to approve your account."
            return redirect(f'/login?msg={msg}')
            
        # FIX 2: Catch duplicate ID errors from BOTH SQLite and PostgreSQL
        except (sqlite3.IntegrityError, psycopg2.IntegrityError):
            return render_template('login.html', view='register', error="Administrator ID already exists.")
        finally:
            conn.close()
            
    return render_template('login.html', view='register')

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        if 'fetch_question' in request.form:
            username = request.form.get('username')
            conn = get_db_connection()
            admin = conn.execute('SELECT security_question FROM admins WHERE username = ?', (username,)).fetchone()
            conn.close()
            
            if admin:
                return render_template('login.html', view='forgot', step=2, username=username, question=admin['security_question'])
            else:
                return render_template('login.html', view='forgot', step=1, error="Administrator ID not found.")
                
        elif 'reset_password' in request.form:
            username = request.form.get('username')
            answer = request.form.get('security_answer').lower().strip()
            new_password = request.form.get('new_password')
            
            conn = get_db_connection()
            admin = conn.execute('SELECT security_answer_hash FROM admins WHERE username = ?', (username,)).fetchone()
            
            if admin and check_password_hash(admin['security_answer_hash'], answer):
                new_hash = generate_password_hash(new_password)
                conn.execute('UPDATE admins SET password_hash = ? WHERE username = ?', (new_hash, username))
                conn.commit()
                conn.close()
                return redirect('/login?msg=Password+reset+successful.+Please+login.')
            else:
                conn.close()
                return render_template('login.html', view='forgot', step=2, error="Incorrect security answer.", username=username)

    return render_template('login.html', view='forgot', step=1)

# ==========================================
# WEB DASHBOARD ROUTES
# ==========================================
@app.route('/dashboard', methods=['GET'])
@login_required
def dashboard():
    msg = request.args.get('msg')
    conn = get_db_connection()
    markets = conn.execute('SELECT * FROM market_prices ORDER BY date_updated DESC').fetchall()
    inputs = conn.execute('SELECT * FROM inputs ORDER BY date_updated DESC').fetchall()
    
    agents = []
    pending_agents = []
    if current_user.role == 'main_admin':
        # Split agents into active and pending queues
        agents = conn.execute("SELECT * FROM admins WHERE role = 'agent' AND status = 'approved'").fetchall()
        pending_agents = conn.execute("SELECT * FROM admins WHERE role = 'agent' AND status = 'pending'").fetchall()
        
    conn.close()
    return render_template('dashboard.html', message=msg, markets=markets, inputs=inputs, agents=agents, pending_agents=pending_agents)

@app.route('/admin/settings', methods=['POST'])
@login_required
def update_settings():
    new_username = request.form.get('new_username')
    new_password = request.form.get('new_password')
    new_question = request.form.get('security_question')
    new_answer = request.form.get('security_answer')
    
    conn = get_db_connection()
    try:
        # 1. Update Username, Question, and hashed Answer
        ans_hash = generate_password_hash(new_answer.lower().strip())
        conn.execute('''
            UPDATE admins 
            SET username = ?, security_question = ?, security_answer_hash = ?
            WHERE id = ?
        ''', (new_username, new_question, ans_hash, current_user.id))
        
        # 2. Only update the passcode if they actually typed a new one
        if new_password:
            pwd_hash = generate_password_hash(new_password)
            conn.execute('UPDATE admins SET password_hash = ? WHERE id = ?', (pwd_hash, current_user.id))
            
        conn.commit()
        return redirect('/dashboard?msg=Account+credentials+updated+successfully.')
        
    except sqlite3.IntegrityError:
        # Triggers if they try to change their ID to one that another agent is already using
        return redirect('/dashboard?msg=Error:+That+Administrator+ID+is+already+taken.')
    finally:
        conn.close()

@app.route('/admin/market', methods=['POST'])
@login_required
def update_market_price():
    province = request.form.get('province')
    town = request.form.get('town')
    market_name = request.form.get('market_name')
    price = request.form.get('price')

    conn = get_db_connection()
    conn.execute('''
        INSERT INTO market_prices (province, town, market_name, price_per_ton) 
        VALUES (?, ?, ?, ?) 
        ON CONFLICT(province, market_name) DO UPDATE SET 
        town=excluded.town,
        price_per_ton=excluded.price_per_ton, 
        date_updated=CURRENT_TIMESTAMP
    ''', (province, town, market_name, price))
    
    users = conn.execute('SELECT phone_number FROM users WHERE province = ?', (province,)).fetchall()
    conn.commit()
    conn.close()
    
    phone_numbers = [u['phone_number'] for u in users]
    if phone_numbers:
        alert_msg = f"MaizeConnect ALERT: New maize price at {market_name} in {town} ({province}) is now {price}."
        try:
            sms.send(alert_msg, phone_numbers)
        except Exception:
            pass
            
    return redirect('/dashboard?msg=Market+Price+Updated+and+Farmers+Alerted')

@app.route('/admin/input', methods=['POST'])
@login_required
def update_input_price():
    province = request.form.get('province')
    town = request.form.get('town') 
    supplier = request.form.get('supplier')
    item = request.form.get('item')
    price = request.form.get('price')

    conn = get_db_connection()
    conn.execute('''
        INSERT INTO inputs (province, town, supplier_name, item_name, price) 
        VALUES (?, ?, ?, ?, ?) 
        ON CONFLICT(province, item_name) DO UPDATE SET 
        town=excluded.town,
        supplier_name=excluded.supplier_name,
        price=excluded.price, 
        date_updated=CURRENT_TIMESTAMP
    ''', (province, town, supplier, item, price))
    conn.commit()
    conn.close()
    
    return redirect('/dashboard?msg=Input+Price+Updated+Successfully')

@app.route('/admin/market/delete/<int:market_id>', methods=['POST'])
@login_required
def delete_market(market_id):
    conn = get_db_connection()
    conn.execute('DELETE FROM market_prices WHERE id = ?', (market_id,))
    conn.commit()
    conn.close()
    return redirect('/dashboard?msg=Specific+market+removed+successfully.')

@app.route('/admin/input/delete/<int:input_id>', methods=['POST'])
@login_required
def delete_input(input_id):
    conn = get_db_connection()
    conn.execute('DELETE FROM inputs WHERE id = ?', (input_id,))
    conn.commit()
    conn.close()
    return redirect('/dashboard?msg=Specific+input+removed+successfully.')

# --- NEW APPROVAL ROUTE ---
@app.route('/admin/agent/approve/<int:agent_id>', methods=['POST'])
@login_required
def approve_agent(agent_id):
    if current_user.role != 'main_admin':
        return redirect('/dashboard?msg=UNAUTHORIZED+ACTION')
        
    conn = get_db_connection()
    conn.execute("UPDATE admins SET status = 'approved' WHERE id = ?", (agent_id,))
    conn.commit()
    conn.close()
    return redirect('/dashboard?msg=Agent+approved+successfully.')

@app.route('/admin/agent/delete/<int:agent_id>', methods=['POST'])
@login_required
def delete_agent(agent_id):
    if current_user.role != 'main_admin':
        return redirect('/dashboard?msg=UNAUTHORIZED+ACTION')
        
    conn = get_db_connection()
    conn.execute('DELETE FROM admins WHERE id = ?', (agent_id,))
    conn.commit()
    conn.close()
    return redirect('/dashboard?msg=Agent+rejected/removed.')

@app.route('/admin/sync_weather', methods=['POST'])
@login_required
def admin_sync_weather():
    fetch_national_weather()
    return redirect('/dashboard?msg=National+Weather+Sync+Complete')

# ==========================================
# CORE USSD ROUTING (UPGRADED AUTHENTICATION)
# ==========================================
@app.route('/ussd', methods=['POST'])
def ussd_callback():
    phone_number = request.values.get("phoneNumber", None)
    text = request.values.get("text", "default")

    text_array = text.split('*') if text else []
    if "" in text_array:
        text_array.remove("")

    user = get_user(phone_number)
    response = ""

    # Security Questions Dictionary
    SEC_QUESTIONS = {
        '1': 'What city were you born in?',
        '2': "What is your mother's maiden name?",
        '3': 'What was the name of your first school?'
    }

    # ==========================================
    # FLOW A: UNREGISTERED USER
    # ==========================================
    if not user:
        if len(text_array) == 0:
            response = "CON Welcome to Maize-Connect.\nReply 1 to Register."
        elif len(text_array) == 1 and text_array[0] == '1':
            response = "CON Enter your full name:"
        elif len(text_array) == 2 and text_array[0] == '1':
            response = "CON Create a 4-digit PIN:"
        elif len(text_array) == 3 and text_array[0] == '1':
            response = "CON Select Province:\n1.Harare \n2.Bulawayo \n3.Manicaland \n4.Midlands \n5.Masvingo \n6.Mash West \n7.Mash Central \n8.Mash East \n9.Mat South \n10.Mat North"
        elif len(text_array) == 4 and text_array[0] == '1':
            response = "CON Select Security Question (For PIN Recovery):\n1. City of birth?\n2. Mother's maiden name?\n3. First school?"
        elif len(text_array) == 5 and text_array[0] == '1':
            response = "CON Enter your answer:"
        elif len(text_array) == 6 and text_array[0] == '1':
            full_name = text_array[1]
            pin = text_array[2]
            loc_choice = text_array[3]
            q_choice = text_array[4]
            ans = text_array[5]
            
            # --- NEW SECURITY UPGRADE: PIN VALIDATION (REGISTRATION) ---
            if not (pin.isdigit() and len(pin) == 4):
                response = "END Registration failed. Your PIN must be exactly 4 numbers. Please try again."
            # -----------------------------------------------------------
            elif loc_choice in LOCATIONS and q_choice in SEC_QUESTIONS:
                town, province = LOCATIONS[loc_choice]
                sec_q = SEC_QUESTIONS[q_choice]
                create_user(phone_number, full_name, pin, province, town, sec_q, ans)
                response = f"END Registration successful for {province}. Dial *384*30858# to login."
            else:
                response = "END Invalid selection. Try again."
        else:
            response = "END Invalid input. Please try again."

    # ==========================================
    # FLOW B: REGISTERED USER
    # ==========================================
    else:
        if len(text_array) == 0:
            response = "CON Welcome back.\n1. Login\n2. Forgot PIN\n3. Change Details"
            
        # --- BRANCH 1: STANDARD LOGIN ---
        elif text_array[0] == '1':
            if len(text_array) == 1:
                response = "CON Enter your 4-digit PIN:"
            elif len(text_array) >= 2:
                entered_pin = text_array[1]
                
                if entered_pin == user['pin']:
                    if len(text_array) == 2:
                        response = "CON Select Service:\n1. Maize Prices\n2. Weather\n3. Inputs\n4. Sell Maize\n5. Buy Maize"
                    else:
                        service_choice = text_array[2]
                        
                        if service_choice in ['1', '2', '3'] and len(text_array) == 3:
                            response = "END Your request has been received. You will receive an SMS shortly."
                            threading.Thread(target=send_sms_async, args=(phone_number, service_choice)).start()
                            
                        elif service_choice == '4':
                            if len(text_array) == 3:
                                response = "CON Enter quantity to sell (in Tons):"
                            elif len(text_array) == 4:
                                response = "CON Enter your asking price per Ton ($):"
                            elif len(text_array) == 5:
                                quantity = text_array[3]
                                price = text_array[4]
                                
                                conn = get_db_connection()
                                conn.execute('''
                                    INSERT INTO listings (phone_number, province, town, quantity_tons, price_per_ton, status) 
                                    VALUES (?, ?, ?, ?, ?, 'OPEN')
                                ''', (phone_number, user['province'], user['town'], quantity, price))
                                conn.commit()
                                conn.close()
                                
                                response = f"END Listing successful. Buyers in {user['province']} will be notified."
                                demo_msg = f"MaizeConnect: Your listing for {quantity}T at ${price}/T is live in {user['province']}."
                                try:
                                    sms.send(demo_msg, [phone_number])
                                except Exception:
                                    pass
                                    
                        elif service_choice == '5':
                            if len(text_array) == 3:
                                response = "END Searching for available maize in your region. You will receive an SMS shortly."
                                
                                def send_buyer_sms(buyer_phone, province):
                                    conn = get_db_connection()
                                    available_maize = conn.execute('''
                                        SELECT phone_number, quantity_tons, price_per_ton, town 
                                        FROM listings 
                                        WHERE province = ? AND status = 'OPEN' 
                                        ORDER BY date_listed DESC LIMIT 3
                                    ''', (province,)).fetchall()
                                    conn.close()
                                    
                                    if available_maize:
                                        msg = f"MaizeConnect ({province}) For Sale:\n"
                                        for row in available_maize:
                                            msg += f"- {row['quantity_tons']}T @ ${row['price_per_ton']}/T in {row['town']} (Call: {row['phone_number']})\n"
                                    else:
                                        msg = f"MaizeConnect: No open maize listings in {province} currently."
                                    try:
                                        sms.send(msg, [buyer_phone])
                                    except Exception:
                                        pass

                                threading.Thread(target=send_buyer_sms, args=(phone_number, user['province'])).start()
                                
                        else:
                            response = "END Invalid selection."
                else:
                    response = "END Invalid PIN. Please try again."

        # --- BRANCH 2: FORGOT PIN ---
        elif text_array[0] == '2':
            if len(text_array) == 1:
                response = f"CON Security Question:\n{user['security_question']}\n\nEnter your answer:"
            elif len(text_array) == 2:
                entered_ans = text_array[1].lower().strip()
                if entered_ans == user['security_answer']:
                    response = "CON Answer Correct. Enter your NEW 4-digit PIN:"
                else:
                    response = "END Incorrect answer. Access denied."
            elif len(text_array) == 3:
                entered_ans = text_array[1].lower().strip()
                new_pin = text_array[2]
                
                # --- NEW SECURITY UPGRADE: PIN VALIDATION (FORGOT PIN) ---
                if not (new_pin.isdigit() and len(new_pin) == 4):
                    response = "END PIN reset failed. Your NEW PIN must be exactly 4 numbers. Please try again."
                # ---------------------------------------------------------
                elif entered_ans == user['security_answer']:
                    conn = get_db_connection()
                    conn.execute('UPDATE users SET pin = ? WHERE phone_number = ?', (new_pin, phone_number))
                    conn.commit()
                    conn.close()
                    response = "END PIN reset successfully. Please redial to login."
                else:
                    response = "END Access denied."

        # --- BRANCH 3: CHANGE PROFILE DETAILS ---
        elif text_array[0] == '3':
            if len(text_array) == 1:
                response = "CON Security Check. Enter your 4-digit PIN:"
            elif len(text_array) >= 2:
                entered_pin = text_array[1]
                
                if entered_pin == user['pin']:
                    if len(text_array) == 2:
                        response = "CON What do you want to change?\n1. Change Name\n2. Change Region"
                    elif len(text_array) == 3:
                        change_choice = text_array[2]
                        if change_choice == '1':
                            response = "CON Enter your new Full Name:"
                        elif change_choice == '2':
                            response = "CON Select New Province:\n1.Harare \n2.Bulawayo \n3.Manicaland \n4.Midlands \n5.Masvingo \n6.Mash West \n7.Mash Central \n8.Mash East \n9.Mat South \n10.Mat North"
                        else:
                            response = "END Invalid selection."
                    elif len(text_array) == 4:
                        change_choice = text_array[2]
                        new_value = text_array[3]
                        
                        conn = get_db_connection()
                        if change_choice == '1':
                            conn.execute('UPDATE users SET full_name = ? WHERE phone_number = ?', (new_value, phone_number))
                            response = f"END Name successfully updated to {new_value}."
                        elif change_choice == '2':
                            if new_value in LOCATIONS:
                                town, province = LOCATIONS[new_value]
                                conn.execute('UPDATE users SET town = ?, province = ? WHERE phone_number = ?', (town, province, phone_number))
                                response = f"END Region successfully updated to {province}."
                            else:
                                response = "END Invalid region selection."
                        conn.commit()
                        conn.close()
                else:
                    response = "END Invalid PIN. Access denied."
        
        else:
            response = "END Invalid Selection."

    return make_response(response, 200, {"content-type": "text/plain"})

if __name__ == '__main__':
    # ==========================================
    # ENTERPRISE AUTO-SYNC ENGINE
    # ==========================================
    print("Initializing Background Scheduler...")
    
    # daemon=True ensures the background threads don't block the server from stopping
    scheduler = BackgroundScheduler(daemon=True)
    
    # 1. Schedule daily sync at exactly 6:00 AM every morning (Cron Job)
    scheduler.add_job(fetch_national_weather, 'cron', hour=6, minute=0)
    
    # 2. Force an immediate sync right now on server startup
    scheduler.add_job(fetch_national_weather, 'date', run_date=datetime.now())
    
    scheduler.start()

    # Ensure the scheduler shuts down safely when you stop the Flask server (Ctrl+C)
    atexit.register(lambda: scheduler.shutdown())
    
    print("Auto-Sync Engine Active. Weather will sync now, and then daily at 6:00 AM.")

    # Start the Flask server (reloader disabled to prevent duplicate scheduler jobs)
    app.run(port=8000, debug=True, use_reloader=False)