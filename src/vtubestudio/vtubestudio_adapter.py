# %%
from websocket import create_connection, WebSocketException
import configparser
import json
import os

class VtubeStudioAdapter:
    def __init__(self,base_dir,vts_allow_flag):
        config = configparser.ConfigParser()
        settings_path = os.path.join(base_dir, 'settings', 'settings.ini')
        config.read(settings_path, encoding='utf-8')
        self.vts_ws_host = config.get('VTS', 'vts_ws_host',fallback="127.0.0.1")
        self.vts_ws_port = config.get('VTS', 'vts_ws_port',fallback="8001")
        self.pre_hotkeyId = None
        self.connect_websocket()
        if self.ws:
            self.authentication_token = self._request_authentication_token()
            if self.authentication_token:
                authenticated = self._request_authentication(self.authentication_token)
                vts_allow_flag.put(0)
            else:
                authenticated = False
                vts_allow_flag.put(1)
            print(authenticated)
            
    def connect_websocket(self):
        try:
            self.ws = create_connection('ws://' + self.vts_ws_host + ':' + self.vts_ws_port)
        except WebSocketException as e:
            print(f"WebSocket connection error: {e}")
            self.ws = None

    def _request_authentication_token(self):
        authentication_token_request = {
            "apiName": "VTubeStudioPublicAPI",
            "apiVersion": "1.0",
            "requestID": "TokenRequestID",
            "messageType": "AuthenticationTokenRequest",
            "data": {
                "pluginName": "AIVsystem_Plugin",
                "pluginDeveloper": "master",
                "pluginIcon": None
            }
        }
        self.ws.send(json.dumps(authentication_token_request))
        response = self.ws.recv()
        print("Received '%s'" % response)
        json_response = json.loads(response)
        if json_response['messageType'] == 'AuthenticationTokenResponse':
            AuthenticationToken = json_response["data"]["authenticationToken"]
            print(f"Token: {AuthenticationToken}")
        else:
            AuthenticationToken = None
        return AuthenticationToken
        
    def _request_authentication(self,authenticationToken):
        authentication_request = {
            "apiName": "VTubeStudioPublicAPI",
            "apiVersion": "1.0",
            "requestID": "AuthenticationRequestID",
            "messageType": "AuthenticationRequest",
            "data": {
                "pluginName": "AIVsystem_Plugin",
                "pluginDeveloper": "master",
                "authenticationToken": authenticationToken
            }
        }
        self.ws.send(json.dumps(authentication_request))
        response = self.ws.recv()
        print("Received '%s'" % response)
        json_response = json.loads(response)
        if json_response['messageType'] == 'AuthenticationResponse':
            return json_response["data"]["authenticated"]
        else:
            return False

    def send_request(self, hotkeyId):
        print("hotkeyId:",hotkeyId)
        print("pre_hotkeyId:",self.pre_hotkeyId)
        def excute(hotkeyId):
            request = {
                "apiName": "VTubeStudioPublicAPI",
                "apiVersion": "1.0",
                "requestID": "SomeID",
                "messageType": "HotkeyTriggerRequest",
                "data": {
                    "hotkeyID": hotkeyId,
                    "itemInstanceID": None
                }
            }
            request = json.dumps(request)
            self.ws.send(request)
            response = self.ws.recv()
            print("Received '%s'" % response)
        
        if not self.pre_hotkeyId:
            excute(hotkeyId)
            self.pre_hotkeyId = hotkeyId
        elif self.pre_hotkeyId == hotkeyId:
            print("pass")
            pass
        else:
            excute(self.pre_hotkeyId)
            excute(hotkeyId)
            self.pre_hotkeyId = hotkeyId

    def close_websocket(self):
        self.ws.close()
        self.ws = None
        pass

    def _is_connected(self):
        return self.ws and self.ws.connected

    def ensure_connection(self):
        #if not self._is_connected():
        #    print("WebSocket is disconnected. Attempting to reconnect...")
        self.connect_websocket()
        if self.ws:
            authenticated = self._request_authentication(self.authentication_token)
            print(authenticated)

    def get_hotkey_list(self):
        request = {
            "apiName": "VTubeStudioPublicAPI",
            "apiVersion": "1.0",
            "requestID": "0000",
            "messageType": "HotkeysInCurrentModelRequest",
            "data": {
                "modelID": None,
                "live2DItemFileName": None
            }
        }
        request = json.dumps(request)
        self.ws.send(request)
        response = self.ws.recv()
        response = json.loads(response)
        converted_data = {
            "current_model_name": response["data"]["modelName"],
            "hotkeys_list": [ 
                {
                    "hotkey_name": hotkey["name"],
                    "file": hotkey["file"],
                    "hotkeyID": hotkey["hotkeyID"]
                } for hotkey in response["data"]["availableHotkeys"]
            ]
        }
        return converted_data

# if __name__ == "__main__":
#     import multiprocessing
#     vts_allow_flag = multiprocessing.Queue()
#     vs = VtubeStudioAdapter(vts_allow_flag)
#     print(vs.get_hotkey_list())
    # i = 1
    # for hotkeyId in ["23883dccdeb2425799738ec84114aef5", "e690e99696ff43d68539a387cd15d039", "e690e99696ff43d68539a387cd15d039", "91a1e2fe72bf4ef2810222d8dcde00cb", "23883dccdeb2425799738ec84114aef5"]:
    #     print("i = ",i)
    #     vs.ensure_connection()
    #     print("connection ok")
    #     vs.send_request(hotkeyId)
    #     print("hotkey ok")
    #     time.sleep(10)
    #     i += 1
    

"""
# Expression file active/deactive list
{
	"apiName": "VTubeStudioPublicAPI",
	"apiVersion": "1.0",
	"requestID": "SomeID",
	"messageType": "ExpressionStateRequest",
	"data": {
		"details": true,
		"expressionFile": "myExpression_optional_1.exp3.json",
	}
}

# Expression file active/deactive trigger
{
	"apiName": "VTubeStudioPublicAPI",
	"apiVersion": "1.0",
	"requestID": "SomeID",
	"messageType": "ExpressionActivationRequest",
	"data": {
		"expressionFile": "myExpression_1.exp3.json",
		"active": true
	}
}

# Hot Key list
{
	"apiName": "VTubeStudioPublicAPI",
	"apiVersion": "1.0",
	"requestID": "SomeID",
	"messageType": "HotkeysInCurrentModelRequest",
	"data": {
		"modelID": "Optional_UniqueIDOfModel",
		"live2DItemFileName": "Optional_Live2DItemFileName"
	}
}

# Hot Key trriger
{
	"apiName": "VTubeStudioPublicAPI",
	"apiVersion": "1.0",
	"requestID": "SomeID",
	"messageType": "HotkeyTriggerRequest",
	"data": {
		"hotkeyID": "HotkeyNameOrUniqueIdOfHotkeyToExecute",
		"itemInstanceID": "Optional_ItemInstanceIdOfLive2DItemToTriggerThisHotkeyFor"
	}
}
"""
# %%
