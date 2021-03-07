import cx_Oracle
import os
import codecs
##import zlib
from flask import Flask,render_template,request
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding

con=cx_Oracle.connect("username/password@localhost")
cursor=con.cursor()

app=Flask(__name__)

relative_path=os.path.relpath("..\\files")


#app url name and fuction name below it should be same
@app.route('/',methods=["GET"])
def index():
	return render_template("index.html")

@app.route('/registration',methods=["GET","POST"])
def registration():       
        return render_template("registration.html")

@app.route('/register',methods=["POST"])
def register():
        name=request.form['name']
        password=request.form['pass']
        print(name)
        #database shows error when same name given in userfield
        command="create table "+name+"(status varchar2(10),message varchar2(50),hashed_val varchar2(4000),to_from varchar2(10),encrypt_msg varchar2(4000))";
        print(command)
        cursor.execute(command)
        print("value inserted successfully")
        #con.commit()

        command1="insert into CDACLogin values('"+name+"','"+password+"')";
        print(command1)
        cursor.execute(command1)
        print("Login table updated successfully")
        con.commit()
        print("Done registering")

        private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
        )
        pem_private = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
        )
        
        public_key = private_key.public_key()
        pem_public=public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        
        filename_private=name+"private_key.pem"
        filename_public=name+"public_key.pem"
        final_path_private=os.path.join(relative_path,filename_private)
        final_path_public=os.path.join(relative_path,filename_public)
        print(final_path_private,final_path_public)

        with open(final_path_private, 'wb') as f:
            f.write(pem_private)
        with open(final_path_public, 'wb') as f1:
            f1.write(pem_public)

        print("key saved")
        return render_template("Dashboard.html")

@app.route('/login',methods=["POST"])
def login():
        user=request.form['uname']
        password=request.form['pass']
        print(user+password)
        command="select * from CDACLogin where name='"+user+"'";
        for row in cursor.execute(command):
                for i in range (len(row)):
                        print(i)
                        if(i==1):
                                if(row[i]==password):
                                        return render_template("Dashboard.html")
                                else:
                                        return render_template("Error.html")
        
        return 'got credentials'

@app.route('/ViewMsg',methods=["GET"])
def ViewMsg():
        return render_template("ViewMsg.html")

@app.route('/NewMsg',methods=["GET"])
def NewMsg():
        return render_template("NewMsg.html")

@app.route('/view',methods=["POST"])
def view():
        uname=request.form['name']
        password=request.form['pass']
        print(uname)
        command="select * from CDACLogin where name='"+uname+"'";
        for row in cursor.execute(command):
                for i in range (len(row)):
                        print(i)
                        if(i==1):
                                if(row[i]==password):
                                        cmd="select * from "+uname;
                                        messages=[]
                                        for row in cursor.execute(cmd):
                                                for i in range (len(row)):
                                                        if(i==2):
                                                                msg=row[1]
                                                                print(msg)
                                                                byte_msg=bytes(msg,'utf-8')
                                                                filename=uname+"private_key.pem"
                                                                final_path=os.path.join(relative_path,filename)
                                                                print(final_path)
                                                                
                                                                print(row[i])
                                                                if(byte_msg.hex()==row[i]):
                                                                        print("equal")
                                                                        print(row[1])
                                                                        with open(final_path, "rb") as key_file:
                                                                                 private_key = serialization.load_pem_private_key(
                                                                                         key_file.read(),
                                                                                         password=None,
                                                                                         backend=default_backend()
                                                                                 )
                                                                        encrypted_hex=row[4]
                                                                        print(encrypted_hex)
                                                                        encrypted=bytearray.fromhex(encrypted_hex)
                                                                        encrypted_final=bytes(encrypted)
                                                                        original_message = private_key.decrypt(
                                                                                encrypted_final,
                                                                                padding.OAEP(
                                                                                       mgf=padding.MGF1(algorithm=hashes.SHA256()),
                                                                                       algorithm=hashes.SHA256(),
                                                                                       label=None
                                                                                   )
                                                                               )
                                                                        
                                                                        print(codecs.decode(original_message))
                                                                        messages.append((codecs.decode(original_message),row[3]))
                                                                else:
                                                                        print("corruption detected")
                                                                        messages.append(("corrupted message",row[3]))
                                        
                                                                                
        print(messages)
        code=displayMsg(messages)
        return (code)

def displayMsg(messages):
        htmlCode="<body style='background-color:#03506f;'><h1 style='padding:0.5rem 2rem;text-align:center;color:white'>You have recieved the following messages:</h1><div style=''><ul style='padding:1rem;border-radius:10px;border:1px solid black;margin:0 2rem;width:50%;position:relative;left:20%;background-color:#bbdfc8'>"
        count=0
        for i in messages:
                htmlCode=htmlCode+"<li style='padding:1rem;border:1px solid black;margin:0.5rem;width:70%;position:relative;top:0;left:12%;background-color:beige;border-radius:10px'><soan style='font-weight:700'>Message</span> - "+i[0]+"<br> <br><span style='font-weight:700'>From</span> - "+i[1]+"</li>"
                count=count+1
                if(count==len(messages)):
                        htmlCode=htmlCode+"</ul></div></body>"

        return htmlCode
                
                

@app.route('/new',methods=["POST"])
def new():
        uname=request.form['uname']
        recipient=request.form['recipient']
        msg=request.form['message']
        byte_msg=bytes(msg,'utf-8')

        filename=recipient+"public_key.pem"
        final_path=os.path.join(relative_path,filename)
        print(final_path)
        with open(final_path, "rb") as key_file:
                public_key = serialization.load_pem_public_key(
                key_file.read(),
                backend=default_backend()
                )
                print("reading keys done")
        encrypted = public_key.encrypt(
                byte_msg,
                padding.OAEP(
                        mgf=padding.MGF1(algorithm=hashes.SHA256()),
                        algorithm=hashes.SHA256(),
                        label=None
                )
        )
        
##        length=len(encrypted)
##        cipher1=encrypted[0:int(length/2)]
##        print(cipher1)
        command="insert into "+recipient+"(status,message,hashed_val,to_from,encrypt_msg) values('recieve','"+msg+"','"+byte_msg.hex()+"','"+uname+"','"+encrypted.hex()+"')";
        print(command)
        cursor.execute(command)
        con.commit()
        print("values inserted successfully")
        print("msg sent successfully")
        return render_template("Dashboard.html")

    
if __name__=="__main__":
    app.run(debug=True)
