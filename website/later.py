#  # Check for & store school code in session variable
#     school_code = id_info.get('hd')
#     if school_code == None:
#         session['school_code'] = None
#     else:
#         session['school_code'] = school_code
#     print(session['school_code'])

#  # If the user logged in with a school account
#         if school_code != None:
                
#                 # If the school exists
#                 if db.session.query(School).filter(School.code == school_code).count() != 0:
#                     school_id = School.query.filter_by(code = session['school_code']).first().id
#                     session['school_id'] = school_id
                
#                 # Else make a new school
#                 else: 
#                     new_school = School(session['school_code'], session['school_code'], [])
#                     db.session.add(new_school)



# @app.route('/edit-profile', methods=['GET','POST'])
# def edit_profile():
#     if request.method == 'POST':
#         name = request.form['name']
#         school = request.form['school']
#         major = request.form['major']
        
        
#         user = User.query.filter_by(email=session['email']).first()
#         user.name = name
#         # user.school = school
#         user.major = major
#         session['name'] = name
        
#         school_now = School.query.filter_by(name=school).first()
#         school_id = school_now.id
        
#         user.school_id = school_id
#         db.session.commit()
#         return redirect('/view-profile')
#     else:
#         schools = School.query.all()
#         return render_template('edit-profile.html', schools = schools)