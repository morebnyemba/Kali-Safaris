# whatsappcrm_backend/flows/definitions/date_picker_whatsapp_flow.py

WHATSAPP_FLOW_DATE_PICKER = {
    "name": "date_picker_whatsapp",
    "friendly_name": "Generic Date Picker",
    "description": "A reusable WhatsApp interactive flow for selecting single or range of dates.",
    "flow_json": {
        "version": "3.0",
        "routing_model": {
            "GUEST": ["Date_Picker_Screen"]
        },
        "screens": [
            {
                "id": "Date_Picker_Screen",
                "title": "Select Date(s)",
                "terminal": False,
                "data": {},
                "layout": {
                    "type": "SingleColumnLayout",
                    "children": [
                        {
                            "type": "TextSubheading",
                            "text": "{{ date_picker_config.title | default('Choose Your Dates') }}"
                        },
                        {
                            "type": "TextBody",
                            "text": "{{ date_picker_config.description | default('Please select the date or date range.') }}"
                        },
                        {
                            "type": "DatePicker",
                            "name": "selected_date",
                            "mode": "{{ date_picker_config.type | default('single') }}",
                            "label": "{{ date_picker_config.label | default('Select Date(s)') }}",
                            "range": {
                                "min": "{{ date_picker_config.range.min | default('') }}",
                                "max": "{{ date_picker_config.range.max | default('') }}"
                            }
                        },
                        {
                            "type": "Footer",
                            "label": "{{ date_picker_config.flow_cta | default('Confirm Selection') }}",
                            "on_click_action": {
                                "name": "complete",
                                "payload": {}
                            }
                        }
                    ]
                }
            }
        ]
    }
}