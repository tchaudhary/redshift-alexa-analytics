import os
import boto3
import psycopg2
import psycopg2.extras
import sys

# --------------- Helpers that build all of the responses ----------------------

def build_speechlet_response(title, output, reprompt_text, should_end_session):
    return {
        'outputSpeech': {
            'type': 'PlainText',
            'text': output
        },
        'card': {
            'type': 'Simple',
            'title': "SessionSpeechlet - " + title,
            'content': "SessionSpeechlet - " + output
        },
        'reprompt': {
            'outputSpeech': {
                'type': 'PlainText',
                'text': reprompt_text
            }
        },
        'shouldEndSession': should_end_session
    }


def build_response(session_attributes, speechlet_response):
    return {
        'version': '1.0',
        'sessionAttributes': session_attributes,
        'response': speechlet_response
    }

# --------------- Functions that control the skill's behavior ------------------

def get_welcome_response():
    """ If we wanted to initialize the session to have some attributes we could
    add those here
    """

    session_attributes = {}
    card_title = "Welcome"
    speech_output = os.environ["greeting_msg"]
    # If the user either does not reply to the welcome message or says something
    # that is not understood, they will be prompted again with this text.
    reprompt_text = "to hear available metrics, ask Alexa: tell me my available metrics."
    should_end_session = False
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))


def handle_session_end_request():
    card_title = "Session Ended"
    speech_output = os.environ["exit_msg"]
    # Setting this to true ends the session and exits the skill.
    should_end_session = True
    return build_response({}, build_speechlet_response(
        card_title, speech_output, None, should_end_session))

def query_redshift_metric(metric,dt):

  REDSHIFT_DATABASE = os.environ['REDSHIFT_DATABASE']
  REDSHIFT_USER = os.environ['REDSHIFT_USER']
  REDSHIFT_PASSWD = os.environ['REDSHIFT_PASSWD']
  REDSHIFT_PORT = os.environ['REDSHIFT_PORT']
  REDSHIFT_ENDPOINT = os.environ['REDSHIFT_ENDPOINT']
  REDSHIFT_CLUSTER = os.environ['REDSHIFT_CLUSTER']
  REDSHIFT_QUERY = "call get_alexa_metric('"+metric+"','"+dt+" 00:00:00')"

  try:
    conn = psycopg2.connect(
    dbname=REDSHIFT_DATABASE,
    user=REDSHIFT_USER,
    #creds['DbUser'],
    password=REDSHIFT_PASSWD,
    #creds['DbPassword'],
    port=REDSHIFT_PORT,
    host=REDSHIFT_ENDPOINT)
  except Exception as ERROR:
    print("Connection Issue: " + str(ERROR))
    sys.exit(1)

  try:
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute(REDSHIFT_QUERY)
    query_results = cursor.fetchall()
    result = query_results
    cursor.close()
    conn.commit()
    conn.close()
  except Exception as ERROR:
    print("Execution Issue: " + str(ERROR))

  return result

def get_metric_from_session(intent, session):
    session_attributes = {}
    reprompt_text = None
    metric_value = query_redshift_metric(intent['slots'][os.environ["slot_name"]]['value'].upper(),intent['slots'][os.environ["date_slot"]]['value'])
    if metric_value:
        speech_output = "The value of " + intent['slots'][os.environ["slot_name"]]['value'] + " for " + intent['slots'][os.environ["date_slot"]]['value'] + " is " + str(metric_value[0][0]) 
        should_end_session = True
    else:
        speech_output = "I'm not sure what that metric is. " \
                        "Please ask for another metric"
        should_end_session = False

    # Setting reprompt_text to None signifies that we do not want to reprompt
    # the user. If the user does not respond or says something that is not
    # understood, the session will end.
    return build_response(session_attributes, build_speechlet_response(
        intent['name'], speech_output, reprompt_text, should_end_session))

def get_available_metric_list(intent, session):
    session_attributes = {}
    reprompt_text = None
    metric_value = query_redshift_metric(intent['slots'][os.environ["list_slot"]]['value'].upper(),'2019-01-01') #passing default date since date is required input parameter for stored procedure
    if metric_value:
        speech_output = "Here are your available metrics " + str(metric_value)
        should_end_session = False
    else:
        speech_output = "I didnt get that"
        should_end_session = False

    # Setting reprompt_text to None signifies that we do not want to reprompt
    # the user. If the user does not respond or says something that is not
    # understood, the session will end.
    return build_response(session_attributes, build_speechlet_response(
        intent['name'], speech_output, reprompt_text, should_end_session))

# --------------- Events ------------------

def on_session_started(session_started_request, session):
    """ Called when the session starts """

    print("on_session_started requestId=" + session_started_request['requestId']
          + ", sessionId=" + session['sessionId'])

def on_launch(launch_request, session):
    """ Called when the user launches the skill without specifying what they
    want
    """

    print("on_launch requestId=" + launch_request['requestId'] +
          ", sessionId=" + session['sessionId'])
    # Dispatch to your skill's launch
    return get_welcome_response()

def on_intent(intent_request, session):
    """ Called when the user specifies an intent for this skill """

    print("on_intent requestId=" + intent_request['requestId'] +
          ", sessionId=" + session['sessionId'])

    intent = intent_request['intent']
    intent_name = intent_request['intent']['name']

    # Dispatch to your skill's intent handlers
    if intent_name.upper() == os.environ["intent_name"].upper():
        return get_metric_from_session(intent, session)
    elif intent_name.upper() == os.environ["list_intent"].upper():
    	return get_available_metric_list(intent, session)
    elif intent_name == "AMAZON.HelpIntent":
        return get_welcome_response()
    elif intent_name == "AMAZON.CancelIntent" or intent_name == "AMAZON.StopIntent":
        return handle_session_end_request()
    else:
        raise ValueError("Invalid intent")

def on_session_ended(session_ended_request, session):
    """ Called when the user ends the session.

    Is not called when the skill returns should_end_session=true
    """
    print("on_session_ended requestId=" + session_ended_request['requestId'] +
          ", sessionId=" + session['sessionId'])


# --------------- Main handler ------------------


def lambda_handler(event, context):

  try:
    if event['session']['new']:
            on_session_started({'requestId': event['request']['requestId']}, event['session'])
  except KeyError:
    print("Message")
        
  if event['request']['type'] == "LaunchRequest":
    return on_launch(event['request'], event['session'])

  elif event['request']['type'] == "IntentRequest":
        return on_intent(event['request'], event['session'])

  elif event['request']['type'] == "SessionEndedRequest":
        return on_session_ended(metrics_table, event['request'], event['session'])
  
