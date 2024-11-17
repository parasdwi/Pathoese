from flask import Flask, render_template, request, redirect, url_for,jsonify, flash, session
from models import db, Pathology, init_app,Test,PathologyTestPrice,User,PathologyPatient
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, validators
from sqlalchemy.orm import joinedload
from forms import RegistrationForm,LoginForm, PathologyLoginForm
from uuid import uuid4
from datetime import datetime
from flask_bcrypt import check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = 'asdkajhsdklasdjlask'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
init_app(app)


@app.route('/', methods=['GET', 'POST'])
def home():
    return render_template("base.html")

@app.route("/main_login", methods=['GET', 'POST'])
def main_login():
    signup_success = request.args.get('signup_success')
    return render_template("main_login.html", signup_success=signup_success)

@app.route('/user_signup', methods=['GET', 'POST'])
def user_signup():
    form = RegistrationForm()

    if request.method == 'POST':
        if form.validate_on_submit():
            user = User(name=form.name.data, email=form.email.data)
            user.set_password(form.password.data)  # Hash the password

            db.session.add(user)
            db.session.commit()

            flash('Registration successful! You can now log in.', 'success')
            return redirect(url_for('main_login', signup_success=True))

    return render_template('user_signup.html', form=form)


@app.route('/user_login', methods=['GET', 'POST'])
def user_login():
    form = LoginForm()
    error_message = None

    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data

        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            # Log in successful
            session['user'] = {
                'id': user.id,
                'name': user.name,
                'email': user.email
            }
            return redirect(url_for('user_home'))
        else:
            # Login failed
            error_message = 'Invalid email or password. Please try again.'

    return render_template('user_login.html', form=form, error_message=error_message)

@app.route('/user_signout', methods=['GET', 'POST'])
def user_signout():
    # Remove user information from the session
    session.pop('user', None)

    # Optional: Flash a logout message
    flash('You have been successfully logged out.', 'success')

    # Redirect to the main login page or any other desired location
    return redirect(url_for('main_login'))

@app.route('/pathology_login', methods=['GET', 'POST'])
def pathology_login():
    form = PathologyLoginForm()
    error_message = None

    if form.validate_on_submit():
        unique_id = form.unique_id.data
        password = form.password.data

        # Query the database to check if the combination of unique_id and password exists
        pathology = Pathology.query.filter_by(unique_id=unique_id).first()

        if pathology and pathology.check_password(password):
            # Login successful
            flash('Login successful!', 'success')
            # You may want to set up a session or use Flask-Login for more advanced user management
            session['pathology'] = {
                'id': pathology.id,
                'name': pathology.name,
                'area': pathology.area
            }

            return redirect(url_for('pathology_dashboard'))
        
        elif unique_id=="admin" and password=="admin":
            return redirect(url_for('index'))

        else:
            # Login failed
            error_message = 'Invalid unique id or password. Please try again.'

    return render_template('pathology_login.html', form=form, error_message=error_message)

@app.route('/pathology_signout')
def pathology_signout():
    # Remove pathology information from the session
    session.pop('pathology', None)

    # Optional: Flash a logout message
    flash('You have been successfully logged out.', 'success')

    # Redirect to the main pathology login page or any other desired location
    return redirect(url_for('main_login'))

@app.route('/pathology_dashboard', methods=['GET'])
def pathology_dashboard():
    if 'pathology' in session:
        pathology = session['pathology']
        # Get appointments booked with the pathology from the database
        appointments = PathologyPatient.query.filter_by(pathology_id=pathology['id']).filter(PathologyPatient.status != 'Rejected').order_by(PathologyPatient.created_at.desc()).all()

        # Convert datetime objects to date and time strings for display
        for appointment in appointments:
            appointment.date = appointment.date.strftime('%Y-%m-%d')
            appointment.slot = appointment.slot.strftime('%H:%M')

        return render_template('pathology_dashboard.html', pathology=pathology, appointments=appointments)
    else:
        # Redirect to login page if the pathology is not logged in
        return redirect(url_for('pathology_login'))
    
@app.route('/accept_appointment/<int:appointment_id>', methods=['POST'])
def accept_appointment(appointment_id):
    appointment = PathologyPatient.query.get_or_404(appointment_id)
    if appointment:
        appointment.status = 'Accepted'
        db.session.commit()
    return redirect(url_for('pathology_dashboard'))

@app.route('/reject_appointment/<int:appointment_id>', methods=['POST'])
def reject_appointment(appointment_id):
    appointment = PathologyPatient.query.get_or_404(appointment_id)
    if appointment:
        appointment.status = 'Rejected'
        db.session.commit()
    return redirect(url_for('pathology_dashboard'))

@app.route('/user_home', methods=['GET', 'POST'])
def user_home():
    if 'user' in session:
        user = session['user']
        # Get user's appointments from the database
        appointments = (
            db.session.query(PathologyPatient, Pathology)
            .join(PathologyPatient.pathology)  # Join the PathologyPatient to Pathology relationship
            .filter(PathologyPatient.email == user['email'])
            .order_by(PathologyPatient.created_at.desc())
            .all()
        )
        # Convert datetime objects to date and time strings for display
        for appointment, pathology in appointments:
            if isinstance(appointment.date, datetime):
                appointment.date = appointment.date.date()
            if isinstance(appointment.slot, datetime):
                appointment.slot = appointment.slot.time()
        

        return render_template('user_home.html', user=user, appointments=appointments)
    else:
        # Redirect to login page if the user is not logged in
        return redirect(url_for('main_login'))

@app.route('/cancel_appointment/<int:appointment_id>', methods=['POST'])
def cancel_appointment(appointment_id):
    # Assuming you have a model for pathology patients, replace 'PathologyPatient' with your actual model name
    appointment = PathologyPatient.query.get_or_404(appointment_id)

    if appointment:
        # Delete the appointment
        db.session.delete(appointment)
        db.session.commit()

        flash('Appointment canceled successfully', 'success')
    else:
        flash('Appointment not found', 'error')

    return redirect(url_for('user_home'))
    
@app.route('/admin_index')
def index():
    pathologies = Pathology.query.all()
    tests = Test.query.all()
    test_dict = {test.id: test for test in tests}
    return render_template('index.html', pathologies=pathologies,tests=tests,test_dict=test_dict)

@app.route('/add', methods=['GET', 'POST'])
def add_pathology():
    all_tests = Test.query.all()

    if request.method == 'POST':
        name = request.form['name']
        area = request.form['area']
        address = request.form['address']
        password = request.form['password']

        # Generate a unique ID for the new pathology
        unique_id = str(uuid4())[:8]  # Using the first 8 characters of the UUID as the ID

        pathology = Pathology(unique_id=unique_id, name=name, area=area,address=address)
        pathology.set_password(password)

        for test in all_tests:
            test_id = str(test.id)
            if test_id in request.form.getlist('tests_offered'):
                price = float(request.form[f'price_{test_id}'])
                pathology.tests.append(test)
                pathology.test_prices.append(PathologyTestPrice(test_id=test.id, price=price))

        db.session.add(pathology)
        db.session.commit()

        return redirect(url_for('index'))

    return render_template('add.html', all_tests=all_tests)

@app.route('/edit/<int:pathology_id>', methods=['GET', 'POST'])
def edit_pathology(pathology_id):
    pathology = Pathology.query.get(pathology_id)
    all_tests = Test.query.all()

    if request.method == 'POST':
        pathology.name = request.form['name']
        pathology.area = request.form['area']
        pathology.address = request.form['address']
        pathology.password = request.form['password']

        if pathology.password:
            pathology.set_password(pathology.password)

        # Clear existing tests and prices
        pathology.tests.clear()
        PathologyTestPrice.query.filter_by(pathology_id=pathology.id).delete()

        for test in all_tests:
            test_id = str(test.id)
            if test_id in request.form.getlist('tests_offered'):
                price = float(request.form[f'price_{test_id}'])
                pathology.tests.append(test)
                pathology.test_prices.append(PathologyTestPrice(test_id=test.id, price=price))

        db.session.commit()
        return redirect(url_for('index'))

    return render_template('edit.html', pathology=pathology, all_tests=all_tests)

@app.route('/delete/<int:pathology_id>')
def delete_pathology(pathology_id):
    pathology = Pathology.query.get(pathology_id)

    # Deleting associated test prices
    PathologyTestPrice.query.filter_by(pathology_id=pathology.id).delete()

    db.session.delete(pathology)
    db.session.commit()
    return redirect(url_for('index'))


@app.route('/add_test', methods=['GET', 'POST'])
def add_test():
    if request.method == 'POST':
        name = request.form['name']

        new_test = Test(name=name)
        db.session.add(new_test)
        db.session.commit()

        return redirect(url_for('index'))

    return render_template('add_test.html')

@app.route('/edit_test/<int:test_id>', methods=['GET', 'POST'])
def edit_test(test_id):
    test = Test.query.get(test_id)

    if request.method == 'POST':
        test.name = request.form['name']
        db.session.commit()
        return redirect(url_for('index'))

    return render_template('edit_test.html', test=test)

@app.route('/delete_test/<int:test_id>')
def delete_test(test_id):
    test = Test.query.get(test_id)

    # Remove the test from all pathologies
    pathologies = Pathology.query.filter(Pathology.tests.any(id=test_id)).all()
    for pathology in pathologies:
        pathology.tests.remove(test)

    # Delete associated test prices
    PathologyTestPrice.query.filter_by(test_id=test_id).delete()

    # Delete the test itself
    db.session.delete(test)
    db.session.commit()

    return redirect(url_for('index'))


@app.route('/search', methods=['GET', 'POST'])
def search_pathologies():
    if request.method == 'POST':
        test_id = int(request.form['test'])
        area = request.form['area']

        # Perform a query to get matching pathologies based on test type and area
        results = Pathology.query.join(PathologyTestPrice).filter(
            PathologyTestPrice.test_id == test_id,
            Pathology.area.ilike(f'%{area}%')
        ).options(joinedload(Pathology.tests)).all()

        # Extract necessary information for rendering the template
        results_data = []

        for result in results:
            test_name = 'N/A'
            price = 0.0

            # Find the matching test and price for the current pathology
            for test_price in result.test_prices:
                if test_price.test_id == test_id:
                    test_name = test_price.test.name
                    price = test_price.price

            results_data.append({
                'pathology': result,
                'test_name': test_name,
                'price': price
            })

        return render_template('search_results.html', results=results_data)

    # If it's a GET request, render the search form
    tests = Test.query.all()

    # Extract unique test areas
    pathologies = Pathology.query.distinct(Pathology.area).all()
    test_areas = [pathology.area for pathology in pathologies]

    return render_template('search_form.html', tests=tests, test_areas=test_areas)

@app.route('/search_tests', methods=['GET'])
def search_tests():
    term = request.args.get('term', '')
    tests = Test.query.filter(Test.name.ilike(f'%{term}%')).all()
    results = [{'id': test.id, 'text': test.name} for test in tests]
    return jsonify({'results': results})

# New route for fetching areas based on input
@app.route('/search_areas', methods=['GET'])
def search_areas():
    term = request.args.get('term', '')
    
    if term:    
        # Fetch areas based on input
        areas = Pathology.query.filter(Pathology.area.ilike(f'%{term}%')).group_by(Pathology.area).all()
        results = [{'id': area.area, 'text': area.area} for area in areas]
        return jsonify({'results': results})
    
    # If it's a GET request, render the search form
    tests = Test.query.all()

    # Extract unique test areas
    pathologies = Pathology.query.group_by(Pathology.area).all()
    test_areas = [pathology.area for pathology in pathologies]

    return render_template('search_form.html', tests=tests, test_areas=test_areas)

@app.route('/book_pathology/<int:pathology_id>', methods=['GET', 'POST'])
def book_pathology(pathology_id):
    test_name = request.args.get('test_name')  # Get the test_name from the URL parameters
    print(f'Pathology ID: {pathology_id}, Test Name: {test_name}')

    user_info = session.get('user')
    
    if not user_info:
        # If user information is not found in the session, redirect to login
        flash('You need to log in to book an appointment.', 'error')
        return redirect(url_for('user_login'))
    
    user_email = user_info.get('email')

    if request.method == 'POST':
        # Process form data here
        name = request.form['name']
        address = request.form['address']
        phone = request.form['phone']
        age = request.form['age']
        gender = request.form['gender']
        email = user_email
        date_str = request.form['date']
        slot_str = request.form['slot']
        test_name = request.form['test_name']

        date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
        slot_obj = datetime.strptime(slot_str, '%H:%M').time()

        # Create a new PathologyPatient instance
        pathology_patient = PathologyPatient(
            pathology_id=pathology_id,
            test_name=test_name,
            name=name,
            address=address,
            phone=phone,
            age=age,
            gender=gender,
            email=email,
            date=date_obj,
            slot=slot_obj,
        )

        print(f"Test Name: {test_name}")

        db.session.add(pathology_patient)
        db.session.commit()

        flash('Booking successful! We will contact you shortly.', 'success')
        return redirect(url_for('user_home'))

    return render_template('booking_form.html', pathology_id=pathology_id, test_name=test_name)

@app.route('/thank_you')
def thank_you():

    return "<h1>Thank You</h1>"

if __name__ == '__main__':
    app.run(debug=True)

# end of beginning ...
