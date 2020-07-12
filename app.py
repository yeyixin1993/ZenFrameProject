#Flask required imports
from flask import Flask
from flask import render_template
from flask import request
from flask import Response
from functools import wraps
import io
import os
import math

#ics file related imports
"""from icalendar import Calendar, Event
import pytz
import tempfile

#Send Email related imports
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders"""

#General data getter/receiver/handler/displayer imports (numpy, pandas, excel, HTML display, etc.)
import numpy as np
import pandas as pd
"""import xlrd
import xlwt
import xlsxwriter
import openpyxl"""

#Activate json and csv for further use in the assignment
import json
import csv
from datetime import datetime

def check_auth(username, password):
    """This function is called to check if a username /
    password combination is valid.
    """
    return username == 'LXL' and password == '410607'

def authenticate():
    """Sends a 401 response that enables basic auth"""
    return Response(
    'Could not verify your access level for that URL.\n'
    'You have to login with proper credentials', 401,
    {'WWW-Authenticate': 'Basic realm="Login Required"'})

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated



app = Flask(__name__)

#Hyperlink Creation, for welcome_page link redirectory
@app.route('/')
def index():
	return render_template('welcome_page.html',name=None)

@app.route('/curr_meeting')
@requires_auth
def curr_meeting():
    return render_template('curr_meeting.html',name=None)

@app.route('/new_meeting')
@requires_auth
def new_meeting():

    inventory = pd.read_csv('inventory.csv')
    inventory['Quantity'] = inventory['Quantity'].fillna(0)
    inventory.Quantity = inventory.Quantity.astype(int)

    return render_template('new_meeting.html',inventory=inventory)

@app.route('/new_attendee')
@requires_auth
def new_attendee():
    material = pd.read_csv('inventory.csv')
    material['Quantity'] = material['Quantity'].fillna(0)
    material.Quantity = material.Quantity.astype(int)
    return render_template('new_attendee.html',inventory=material)


@app.route('/new_record')
@requires_auth
def new_record():

    inventory = pd.read_csv('inventory.csv')
    inventory['Quantity'] = inventory['Quantity'].fillna(0)
    inventory.Quantity = inventory.Quantity.astype(int)


    pd.DataFrame(inventory['Material'].unique(), columns = ['Material'], index=None).to_csv("material_repo.csv")
    pd.DataFrame(inventory['Unit'].unique(), columns = ['Unit'], index=None).to_csv("unit_repo.csv")

    material = pd.read_csv('material_repo.csv')
    unit = pd.read_csv('unit_repo.csv')
    return render_template('new_record.html',material_repo=material, unit_repo = unit)


@app.route('/tiao_calc')
@requires_auth
def tiao_calc():

    return render_template('tiao_calc.html')    


@app.route('/delete_record')
@requires_auth
def delete_record():
    inventory = pd.read_csv('inventory.csv')

    maxid = max(inventory['ID'])
    mostrecent = inventory.loc[inventory['ID']==maxid]
    return render_template('delete_record.html', inventory=inventory.to_html(), mostrecent=mostrecent.to_html())


#The followings are URLs which actually do the data transfer/creation/modification
@app.route('/curr_meeting_show', methods=['GET'])
@requires_auth
def curr_meeting_show():
    # Show Current Meeting Schedule
    
    inventory = pd.read_csv('inventory.csv', index_col = 'ID')
    inventory['Quantity'] = inventory['Quantity'].fillna(0)
    inventory.Quantity = inventory.Quantity.astype(int)

    return render_template('curr_meeting.html',inventory = inventory.sort_values(by=['Material','Spec']).to_html())

@app.route('/new_meeting_successful',methods=['POST'])
@requires_auth
def new_meeting_successful():
    
    name = request.form.get('name')
    product = request.form.get('product')
    quantity = int(request.form.get('quantity'))
    remarks = request.form.get('remarks')
    time = str(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    
    material,spec = product.split(" ",1)
    
    inv = pd.read_csv('inventory.csv')
    unit = inv.loc[inv['Spec']==spec,"Unit"].values[0]
    inv.loc[inv['Spec']==spec,"Quantity"] -= quantity
    inv.to_csv('inventory.csv', index=False)

    currPeople = pd.read_csv('output_info.csv')
    currPeople = currPeople[["Name","Material","Spec","Quantity","Unit","Remarks","Time"]]
    
    currPeople.loc[-1] = [name,material,spec,quantity,unit,remarks,time]
    currPeople.index = currPeople.index + 1 
    currPeople = currPeople.sort_index()
    
    currPeople.sort_index().to_csv('output_info.csv', index=False)

    outputinfo = pd.read_csv('output_info.csv')
    
    return render_template('meeting_successful.html', peek=outputinfo.head().to_html())


@app.route('/attendee_successful', methods = ['POST'])
@requires_auth
def attendee_successful():
    
    name = request.form.get('name')
    product = request.form.get('product')
    quantity = int(request.form.get('quantity'))
    remarks = request.form.get('remarks')
    time = str(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    
    material,spec = product.split(" ",1)
    
    inv = pd.read_csv('inventory.csv')
    unit = inv.loc[inv['Spec']==spec,"Unit"].values[0]
    
    if math.isnan(inv.loc[inv['Spec']==spec,"Quantity"]):
        inv.loc[inv['Spec']==spec,"Quantity"] = 0

    inv.loc[inv['Spec']==spec,"Quantity"] += quantity
    inv.to_csv('inventory.csv', index=False)

    currPeople = pd.read_csv('input_info.csv')
    currPeople = currPeople[["Name","Material","Spec","Quantity","Unit","Remarks","Time"]]
    
    currPeople.loc[-1] = [name,material,spec,quantity,unit,remarks,time]
    currPeople.index = currPeople.index + 1 
    currPeople = currPeople.sort_index()
    
    currPeople.sort_index().to_csv('input_info.csv', index=False)
    #currPeople.sort_values('Name').to_csv('input_info_sorted.csv')

    inputinfo = pd.read_csv('input_info.csv')

    return render_template('attendee_successful.html', peek=inputinfo.head().to_html())


@app.route('/get_input_info')
@requires_auth
def get_input_info():
    inputinfo = pd.read_csv('input_info.csv')

    return render_template('get_input_info_successful.html', input_info=inputinfo.head().to_html())



@app.route('/new_record_successful', methods = ['POST'])
@requires_auth
def new_record_successful():
    
    material = request.form.get('material')
    spec = request.form.get('spec')
    unit = request.form.get('unit')
    
    inv = pd.read_csv('inventory.csv')
    inv = inv[["ID","Material","Spec","Quantity","Unit"]]
    
    newid = max(inv['ID']) + 1
    inv.loc[-1] = [newid,material,spec,0,unit]
    inv.index = inv.index + 1 
    inv = inv.sort_index()
    
    inv.sort_index().to_csv('inventory.csv', index=False)
    inv.sort_values(by=['Material','Spec']).to_csv('inventory.csv', index=False)

    invinfo = [material,spec,0,unit]

    return render_template('new_record_successful.html', peek=invinfo)



@app.route('/tiaocalc_successful', methods = ['POST'])
@requires_auth
def tiao_calc_successful():

    framelen = float(request.form.get('framelen'))
    framewid = float(request.form.get('framewid'))
    loss = float(request.form.get('loss'))
    framenum = int(request.form.get('framenum'))
    tiaolen = int(request.form.get('tiaolen'))
    tiaounitprice = float(request.form.get('tiaounitprice'))
    manunitprice = float(request.form.get('manunitprice'))
    accessory = float(request.form.get('accessory'))
    package = float(request.form.get('package'))
    
    
    cutlen = framelen + loss
    cutwid = framewid + loss
    totalcutlen = (cutlen + cutwid) * 2 * framenum
    tiaonum = math.ceil(totalcutlen / tiaolen)
        
    tiaoprice = round(tiaonum * tiaounitprice * tiaolen / 100, 2)
    manprice = manunitprice * framenum
    totalprice = math.ceil(tiaoprice + manprice + accessory + package)

    return render_template('tiao_calc_successful.html', tiaonum=tiaonum, totalprice = totalprice)    


@app.route('/delete_record_successful', methods = ['POST'])
@requires_auth
def delete_record_successful():

    #pwd = int(request.form.get('pwd'))

    #if (pwd != 1229):
     #   return '密码错误'

    itemID = int(request.form.get('itemID'))

    
    inv = pd.read_csv('inventory.csv')

    invinfo = inv.loc[inv['ID']==itemID]
    index = invinfo.index.values[0]
    inv = inv.drop(index)
    
    inv.sort_values(by=['Material','Spec']).to_csv('inventory.csv', index=False)

    return render_template('delete_record_successful.html', peek=invinfo.to_html())

"""@app.route('/drop_meeting',methods=['POST'])
def drop_meeting():
    #Drop the meeting, identity verification by email and PIN
    
    email = str(request.form.get('email'))
    pin = int(request.form.get('pin'))
    
    currPeople = pd.read_csv('people_info.csv')
    email_exists = currPeople["Email"].str.contains(email)
    flag = False
    for i in range(len(email_exists)):
        if (email_exists[i]):
            if (int(currPeople["Pin"][i]) == pin):
                flag = True
    
    error = "Cannot found such email & pin combination"
    if (flag == False):
        return json.dumps({ "error": error }), 200
    
    xlsName = "individual_calendar/"+email+".xlsx"
    
    df = pd.read_excel(xlsName)
    csv_schedule = df.to_csv("individual_calendar/"+email+".csv", encoding='utf-8')
    personal_schedule = pd.read_csv("individual_calendar/"+email+".csv")
    
    return render_template('drop_meeting.html', personal_schedule = personal_schedule.to_html())


@app.route('/drop_successful',methods=['POST','GET'])
def drop_successful():
    #Drop the meeting by typing meeting name and email address
    
    name = request.form.get('meeting_name')
    email = request.form.get('email')
    
    currMeeting = pd.read_csv('meeting_info.csv')
    currMeeting_name = currMeeting["Meeting Name"]
    
    for i in range(len(currMeeting_name)):
        meetingName = currMeeting_name[i]
        if (meetingName.replace(" ","") == name.replace(" ","")):
            attendeeList = currMeeting["Attendee Emails"][i]
            attendeeList = attendeeList.replace(email,",")
            attendeeList = attendeeList.replace(",,",",")
            
            if (len(attendeeList) > 0):

                currMeeting["Attendee Emails"][i] = attendeeList
        
    currMeeting.to_csv("meeting_info.csv")
    
    return render_template('drop_meeting_successful.html', name=None)


@app.route('/send_email', methods = ['POST'])
def send_email():
    #Send email to others with attachments of any kind
    error = None
    if (request.method != 'POST'):
        return render_template('send_email.html', error = error)
    
    fromaddr = request.form.get('fromaddr')
    toaddr = request.form.get('toaddr')
    cc = request.form.get('cc')
    pwd = request.form.get('password')
    
    msg = MIMEMultipart()
    
    msg['From'] = fromaddr
    msg['To'] = toaddr
    msg['Cc'] = cc
    msg['Subject'] = "An invitation by Python"
    
    body = request.form.get('body')
    
    msg.attach(MIMEText(body, 'plain'))
    
    filename = request.form.get('attachment')
    attachment = open("*/AgendaProject/"+filename, "rb")
    
    part = MIMEBase('application', 'octet-stream')
    part.set_payload((attachment).read())
    encoders.encode_base64(part)
    part.add_header('Content-Disposition', "attachment; filename= %s" % filename)

    msg.attach(part)

    server = smtplib.SMTP('smtp-mail.outlook.com', 587)
    server.starttls()
    server.login(fromaddr, pwd)
    text = msg.as_string()
    server.sendmail(fromaddr, [toaddr,cc], text)
    server.quit()
    
    return render_template('send_successful.html', name=None)"""
    
if __name__ == '__main__':
    app.run()
