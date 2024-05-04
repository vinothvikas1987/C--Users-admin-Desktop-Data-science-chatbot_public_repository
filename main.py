#Import all dependables

from fastapi import FastAPI,Request,HTTPException
from pymongo import MongoClient
from pydantic import BaseModel
import requests
import razorpay
from typing import Union
import json
from fastapi.responses import JSONResponse
import regex as re
from fastapi import Request
import uuid
import threading
from starlette import status
from google.cloud import dialogflow_v2beta1 as df
from google.protobuf.struct_pb2 import Struct
import logging
import hmac #use this to hash your keys

place_holder = "look into your database"

# Initialize FastAPI app
app = FastAPI()
# Set up MongoDB connection
client = MongoClient() #client DB
db = client[place_holder]#name
collection_members = db[place_holder] #members details
collection_packages = db[place_holder] #package details
new_members_collection = db[place_holder] #new_member details
paid_members = db[place_holder] #payment_received
fail_members = db[place_holder] #failed_payment
thread_local = threading.local()
credential_dict = {
  "type": "service_account",
  "project_id": "c",
  "private_key_id": "",
  "private_key": "",
  "client_email": "",
  "client_id": "",
  "auth_uri": "", #oauth url
  "token_uri": "",
  "auth_provider_x509_cert_url": "",#X509 certificate
  "client_x509_cert_url": "",
  "universe_domain": "googleapis.com"
}

GOOGLE_APPLICATION_CREDENTIALS = json.dumps(credential_dict)
print(type(GOOGLE_APPLICATION_CREDENTIALS))  #vverify credential type
project_id = "" #Header for your project
razorpay_client = razorpay.Client(auth=('[]', '[]')) #Razorpay client authorization key
secret = '12345678'


    
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)
user_info = {}


class RazorpayWebhookEvent(BaseModel):
    event: str
    payload : dict
    

   

#Dialogflow intents
def detect_intent_(data):
    intent = data["queryResult"]["intent"]["displayName"]
    parameters = data["queryResult"]["parameters"]
    return intent,parameters



@app.post("/webhook")
async def webhook(request: Request):
    session_id = str(uuid.uuid4())
    session = session_id
    session_client = df.SessionsClient()
    session_path = session_client.session_path(project_id, session_id)
    print("entered function")
    print(session_id)
    content_type = request.headers.get("Content-Type")
    print(content_type)
    data = await request.json()
    
    

    if "entity" not in data:
        intent,parameters = detect_intent_(data)   
        print(intent)
        print("entering webhook")  
        user_info = getattr(thread_local, 'user_info', {})        
        query = data.get("queryResult", {}).get("queryText", "")
        print("query is {}".format(query))
        print(type(query))

        
        
        
            
        if intent == "getphonenumber":
            print(intent)
            phone_number = parameters["phone-number"][0]
            print(type(phone_number))
            mobile_number = int(phone_number)
            print(mobile_number)
            print(type(mobile_number))
            existing_member = collection_members.find_one({"mobileNumber": str(mobile_number)})
            print(type(existing_member))
            if existing_member:
                user_info[session_id] = {
                        'phone_number': existing_member['mobileNumber'],
                        'name': existing_member['name'],
                        'gender': existing_member['gender']
                }
            
            response_text = f""
            setattr(thread_local, 'user_info', user_info)    
            return JSONResponse(content={"fulfillmentText": [response_text]})




        elif intent == "getphonenumber - yes":
            print(intent)
            p = [user_info[i]['phone_number'] for i in user_info]
            package_details = collection_packages.find_one({"name": "Monthly"})
            pack = package_details['description']
            print(p)
            print(type(p))
            if p:
                g = [user_info[i]['gender'] for i in user_info]
                g = " ".join(g)
                
                n = [user_info[i]['name'] for i in user_info]
                n = " ".join(n)
                        
                if g == "Female":
                    response_text = f""
                elif g == "Male":
                    print(g)
                    response_text = f""
                    print(response_text)
                return JSONResponse(content={"fulfillmentText": [response_text]})
            elif not p:
                print("entered loop")
                response_text = f""
                return JSONResponse(content={"fulfillmentText": [response_text]})




        elif intent == "provide_name_phone":
            print(session_id)
            # # print(intent)
            # phone_number =parameters["phone-number"]
            # name = parameters["person"][0]["name"]        
            # new_member = {"mobileNumber": int(phone_number),"name": str(name)}
            # new_members_collection.insert_one(new_member)
            response_text = f"You are screwed by providing the phone number want to pay?? "
            return JSONResponse(content={"fulfillmentText": [response_text]})
        





        # elif intent == "payment_failed":
        #     print("entered intent loop")
        #     response_text = f"Something went wrong with your payment"   
        #     return JSONResponse(content={"fulfillmentText": [response_text]})

        



        elif intent == "getplan":
            print(intent)
            diet = parameters[""]
            work = parameters[""]
            both = parameters[""]
            g = [user_info[i]['gender'] for i in user_info]
            g = " ".join(g)
            n = [user_info[i]['name'] for i in user_info]
            n = " ".join(n)
            print(n)
            print (diet)
            print(work)
            if both:
                if g == "Male":
                    response_text = f"Go to hell"
            elif diet:
                if g == "Male":
                    response_text = f""
            elif work:
                if g == "Male":
                    response_text = f""

            return JSONResponse(content={"fulfillmentText": [response_text]})



    elif "entity" in data:
        print(session_id)
        data1 = RazorpayWebhookEvent(**data)
        print(type(data1))
        print(data1)
        event_ = data1.event
        payload_ = data1.payload
                
        print(type(event_))
        print(event_)
        
        
        if event_ == "payment.failed":         
            
            payment_id = payload_["payment"]["entity"]["id"]
            email = payload_["payment"]["entity"]["email"]
            phone = payload_["payment"]["entity"]["contact"]
            error = payload_["payment"]["entity"]["error_description"]
            name = payload_["payment"]["entity"]["notes"]["name"]
            details = {name: name, email : email, phone : phone }
            paid_members.insert_one(details)
            logger.info("Received Razorpay webhook request.")                  
            print(f"Payment failed for payment_id: {payment_id}. Error description is {error}")
            print(session_id)

            event_name = "failed_payment"
            # context_name = " provide_name_phone-yes-followup"
        
            # context_dict = {"input_context_names": "projects/raw-is-war-svpc/agent/sessions/-/contexts/payment_initiation",  
            #             "input_context_names": "projects/raw-is-war-svpc/agent/sessions/-/contexts/provide_name_phone-yes-followup"}
            
            
            # intents_client = df.IntentsClient()
            # agents_client = df.AgentsClient()
            # # Define the parent path for your agent
            # parent = agents_client.agent_path(project_id)

            # List intents for the agent
            # intents = intents_client.list_intents(request={"parent":parent})
            # for intent in intents:
            #     print("for loop")
            #     intent_ = intent.display_name
            #     print(type(intent_))
            #     if intent_ == "payment_failed":
            #         print("if")
            #         print(intent)
                    

            event_input = df.EventInput(name=event_name,parameters=Struct(),
            language_code='en' )
            
            # text_input = df.TextInput(text=user_query, language_code='en')
            query_input = df.QueryInput(event=event_input)
            # context = df.types.Context(name=context_name, lifespan_count=2)
            # query_input.output_contexts.append(context)
            
            response = session_client.detect_intent(session=session_path,query_input=query_input)
            print(f"Detected intent: {response.query_result.intent.display_name}")
            print(f"Query text: {response.query_result.query_text}")
            print(f"Response: {response.query_result.fulfillment_text}")
            # response_text = response.query_result.fulfillment_text

            # fulfillmentText = {'fulfillment_text': response_text}
            response_ = ({"status": "ok"})
            # combined = {**response}
           
        
            logger.info("Sending response to Razorpay.")

             
           


        elif event_ == "payment.captured" :

            payment_id = payload_["payment"]["entity"]["id"]
            email = payload_["payment"]["entity"]["email"]
            phone = payload_["payment"]["entity"]["contact"]
            name = payload_["payment"]["entity"]["notes"]["name"]
            details = {name: name, email : email, phone : phone }
            
            
            fail_members.insert_one(details)
            logger.info("Received Razorpay webhook request.")                  
            print(f"Payment is successful for payment_id: {payment_id}")

            event_name = "successful_payment"
            # params = " payment_initiation"
            # user_query = "Payment failed"
            # context_name = "payment_initiation"
            # user_query_with_context = f"{context_name} {user_query}"
            event_input = df.EventInput(name=event_name,parameters=Struct(),
            language_code='en' )
            
            # text_input = df.TextInput(text=user_query, language_code='en')
            query_input = df.QueryInput(event=event_input)
            # query_params = df.QueryParams(Context = params)
            response = session_client.detect_intent(session=session_path,query_input=query_input)
            print(f"Detected intent: {response.query_result.intent.display_name}")
            print(f"Query text: {response.query_result.query_text}")
            print(f"Response: {response.query_result.fulfillment_text}")
            # response_text = response.query_result.fulfillment_text      
            response_ = {"status": "ok"}       
            logger.info("Sending response to Razorpay.")
            
        return response_,200

            
           


    
        

 
    
           
        



