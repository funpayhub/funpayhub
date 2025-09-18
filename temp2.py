from funpayhub.app.properties.properties import FunPayHubProperties


props = FunPayHubProperties()
props.auto_response.add_entry('/my_command')


for i in range(1000):
    props.auto_delivery.add_entry(f'Offer{i}')


props.save()