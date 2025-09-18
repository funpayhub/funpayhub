from funpayhub.app.properties.properties import FunPayHubProperties


props = FunPayHubProperties()
props.auto_response.add_entry('/my_command')
props.save()
