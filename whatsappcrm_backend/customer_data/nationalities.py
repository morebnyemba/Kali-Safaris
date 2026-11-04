"""
Nationalities offered in every traveller form: website checkout, the WhatsApp
traveller form, the WhatsApp text fallback and the dashboard passenger editor.

One list so manifests get consistent values. ZimParks fees differ for
Zimbabweans, other SADC citizens and international visitors, so "Zimbabwean"
must not also appear as "zim" or "Zimbabwe".

The website (public-website/src/lib/nationalities.ts) and the dashboard
(whatsapp-crm-frontend/src/lib/nationalities.js) carry copies;
customer_data/test_nationalities.py fails if they drift from this file.
"""

# Shown first: Zimbabwe, our SADC neighbours, then the main overseas markets.
COMMON = [
    'Zimbabwean', 'South African', 'Zambian', 'Botswanan', 'Namibian', 'Mozambican', 'Malawian',
    'British', 'American', 'German',
]

# Everything else, A–Z (GOV.UK-style demonyms; small territories folded into their country).
OTHERS = [
    'Afghan', 'Albanian', 'Algerian', 'Andorran', 'Angolan', 'Argentine', 'Armenian', 'Australian',
    'Austrian', 'Azerbaijani', 'Bahamian', 'Bahraini', 'Bangladeshi', 'Barbadian', 'Belarusian',
    'Belgian', 'Belizean', 'Beninese', 'Bhutanese', 'Bolivian', 'Bosnian', 'Brazilian', 'Bruneian',
    'Bulgarian', 'Burkinabe', 'Burmese', 'Burundian', 'Cambodian', 'Cameroonian', 'Canadian',
    'Cape Verdean', 'Central African', 'Chadian', 'Chilean', 'Chinese', 'Colombian', 'Comoran',
    'Congolese (Congo)', 'Congolese (DRC)', 'Costa Rican', 'Croatian', 'Cuban', 'Cypriot', 'Czech',
    'Danish', 'Djiboutian', 'Dominican', 'Dutch', 'East Timorese', 'Ecuadorian', 'Egyptian', 'Emirati',
    'Equatorial Guinean', 'Eritrean', 'Estonian', 'Ethiopian', 'Fijian', 'Filipino', 'Finnish',
    'French', 'Gabonese', 'Gambian', 'Georgian', 'Ghanaian', 'Greek', 'Grenadian', 'Guatemalan',
    'Guinean', 'Guinea-Bissauan', 'Guyanese', 'Haitian', 'Honduran', 'Hong Konger', 'Hungarian',
    'Icelandic', 'Indian', 'Indonesian', 'Iranian', 'Iraqi', 'Irish', 'Israeli', 'Italian', 'Ivorian',
    'Jamaican', 'Japanese', 'Jordanian', 'Kazakh', 'Kenyan', 'Kittitian', 'Kosovan', 'Kuwaiti',
    'Kyrgyz', 'Lao', 'Latvian', 'Lebanese', 'Liberian', 'Libyan', 'Liechtensteiner', 'Lithuanian',
    'Luxembourger', 'Macedonian', 'Malagasy', 'Malaysian', 'Maldivian', 'Malian', 'Maltese',
    'Marshallese', 'Mauritanian', 'Mauritian', 'Mexican', 'Micronesian', 'Moldovan', 'Monegasque',
    'Mongolian', 'Montenegrin', 'Moroccan', 'Mosotho (Lesotho)', 'Nauruan', 'Nepalese',
    'New Zealander', 'Nicaraguan', 'Nigerian', 'Nigerien', 'North Korean', 'Norwegian', 'Omani',
    'Pakistani', 'Palauan', 'Palestinian', 'Panamanian', 'Papua New Guinean', 'Paraguayan',
    'Peruvian', 'Polish', 'Portuguese', 'Qatari', 'Romanian', 'Russian', 'Rwandan', 'Salvadoran',
    'Sammarinese', 'Samoan', 'Sao Tomean', 'Saudi', 'Senegalese', 'Serbian', 'Seychellois',
    'Sierra Leonean', 'Singaporean', 'Slovak', 'Slovenian', 'Solomon Islander', 'Somali',
    'South Korean', 'South Sudanese', 'Spanish', 'Sri Lankan', 'St Lucian', 'Sudanese',
    'Surinamese', 'Swazi (Eswatini)', 'Swedish', 'Swiss', 'Syrian', 'Taiwanese', 'Tajik',
    'Tanzanian', 'Thai', 'Togolese', 'Tongan', 'Trinidadian', 'Tunisian', 'Turkish', 'Turkmen',
    'Tuvaluan', 'Ugandan', 'Ukrainian', 'Uruguayan', 'Uzbek', 'Vanuatuan', 'Vatican', 'Venezuelan',
    'Vietnamese', 'Vincentian', 'Yemeni', 'Antiguan', 'I-Kiribati',
]
OTHERS.sort()

NATIONALITIES = COMMON + OTHERS

# "Other" lets someone not on the list type their nationality instead.
OTHER = 'Other'


def nationality_id(name: str) -> str:
    """Stable option id for WhatsApp dropdowns/lists: 'Congolese (DRC)' -> 'congolese_drc'."""
    return '_'.join(''.join(c if c.isalnum() else ' ' for c in name.lower()).split())


_CANONICAL = {n.lower(): n for n in NATIONALITIES}
_CANONICAL.update({nationality_id(n): n for n in NATIONALITIES})


def normalize_nationality(value: str) -> str:
    """
    Canonical name for anything that identifies a listed nationality — the name
    in any case, or its option id ('south_african') — otherwise the text as typed.
    """
    text = ' '.join(str(value or '').split())
    return _CANONICAL.get(text.lower(), text)


def whatsapp_options(include_other: bool = True) -> list[dict]:
    """[{'id': 'zimbabwean', 'title': 'Zimbabwean'}, ...] for WhatsApp form dropdowns."""
    options = [{'id': nationality_id(n), 'title': n} for n in NATIONALITIES]
    if include_other:
        options.append({'id': 'other', 'title': 'Other (type it below)'})
    return options
