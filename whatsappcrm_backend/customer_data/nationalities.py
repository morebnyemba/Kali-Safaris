"""
Nationalities (and countries) offered in every traveller and contact form: website checkout, the WhatsApp
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


# Country for each nationality, so both pickers cover exactly the same places.
COUNTRY_OF = {
    'Zimbabwean': 'Zimbabwe',
    'South African': 'South Africa',
    'Zambian': 'Zambia',
    'Botswanan': 'Botswana',
    'Namibian': 'Namibia',
    'Mozambican': 'Mozambique',
    'Malawian': 'Malawi',
    'British': 'United Kingdom',
    'American': 'United States',
    'German': 'Germany',
    'Afghan': 'Afghanistan',
    'Albanian': 'Albania',
    'Algerian': 'Algeria',
    'Andorran': 'Andorra',
    'Angolan': 'Angola',
    'Antiguan': 'Antigua and Barbuda',
    'Argentine': 'Argentina',
    'Armenian': 'Armenia',
    'Australian': 'Australia',
    'Austrian': 'Austria',
    'Azerbaijani': 'Azerbaijan',
    'Bahamian': 'Bahamas',
    'Bahraini': 'Bahrain',
    'Bangladeshi': 'Bangladesh',
    'Barbadian': 'Barbados',
    'Belarusian': 'Belarus',
    'Belgian': 'Belgium',
    'Belizean': 'Belize',
    'Beninese': 'Benin',
    'Bhutanese': 'Bhutan',
    'Bolivian': 'Bolivia',
    'Bosnian': 'Bosnia and Herzegovina',
    'Brazilian': 'Brazil',
    'Bruneian': 'Brunei',
    'Bulgarian': 'Bulgaria',
    'Burkinabe': 'Burkina Faso',
    'Burmese': 'Myanmar',
    'Burundian': 'Burundi',
    'Cambodian': 'Cambodia',
    'Cameroonian': 'Cameroon',
    'Canadian': 'Canada',
    'Cape Verdean': 'Cape Verde',
    'Central African': 'Central African Republic',
    'Chadian': 'Chad',
    'Chilean': 'Chile',
    'Chinese': 'China',
    'Colombian': 'Colombia',
    'Comoran': 'Comoros',
    'Congolese (Congo)': 'Republic of the Congo',
    'Congolese (DRC)': 'DR Congo',
    'Costa Rican': 'Costa Rica',
    'Croatian': 'Croatia',
    'Cuban': 'Cuba',
    'Cypriot': 'Cyprus',
    'Czech': 'Czechia',
    'Danish': 'Denmark',
    'Djiboutian': 'Djibouti',
    'Dominican': 'Dominican Republic',
    'Dutch': 'Netherlands',
    'East Timorese': 'Timor-Leste',
    'Ecuadorian': 'Ecuador',
    'Egyptian': 'Egypt',
    'Emirati': 'United Arab Emirates',
    'Equatorial Guinean': 'Equatorial Guinea',
    'Eritrean': 'Eritrea',
    'Estonian': 'Estonia',
    'Ethiopian': 'Ethiopia',
    'Fijian': 'Fiji',
    'Filipino': 'Philippines',
    'Finnish': 'Finland',
    'French': 'France',
    'Gabonese': 'Gabon',
    'Gambian': 'Gambia',
    'Georgian': 'Georgia',
    'Ghanaian': 'Ghana',
    'Greek': 'Greece',
    'Grenadian': 'Grenada',
    'Guatemalan': 'Guatemala',
    'Guinean': 'Guinea',
    'Guinea-Bissauan': 'Guinea-Bissau',
    'Guyanese': 'Guyana',
    'Haitian': 'Haiti',
    'Honduran': 'Honduras',
    'Hong Konger': 'Hong Kong',
    'Hungarian': 'Hungary',
    'I-Kiribati': 'Kiribati',
    'Icelandic': 'Iceland',
    'Indian': 'India',
    'Indonesian': 'Indonesia',
    'Iranian': 'Iran',
    'Iraqi': 'Iraq',
    'Irish': 'Ireland',
    'Israeli': 'Israel',
    'Italian': 'Italy',
    'Ivorian': 'Ivory Coast',
    'Jamaican': 'Jamaica',
    'Japanese': 'Japan',
    'Jordanian': 'Jordan',
    'Kazakh': 'Kazakhstan',
    'Kenyan': 'Kenya',
    'Kittitian': 'Saint Kitts and Nevis',
    'Kosovan': 'Kosovo',
    'Kuwaiti': 'Kuwait',
    'Kyrgyz': 'Kyrgyzstan',
    'Lao': 'Laos',
    'Latvian': 'Latvia',
    'Lebanese': 'Lebanon',
    'Liberian': 'Liberia',
    'Libyan': 'Libya',
    'Liechtensteiner': 'Liechtenstein',
    'Lithuanian': 'Lithuania',
    'Luxembourger': 'Luxembourg',
    'Macedonian': 'North Macedonia',
    'Malagasy': 'Madagascar',
    'Malaysian': 'Malaysia',
    'Maldivian': 'Maldives',
    'Malian': 'Mali',
    'Maltese': 'Malta',
    'Marshallese': 'Marshall Islands',
    'Mauritanian': 'Mauritania',
    'Mauritian': 'Mauritius',
    'Mexican': 'Mexico',
    'Micronesian': 'Micronesia',
    'Moldovan': 'Moldova',
    'Monegasque': 'Monaco',
    'Mongolian': 'Mongolia',
    'Montenegrin': 'Montenegro',
    'Moroccan': 'Morocco',
    'Mosotho (Lesotho)': 'Lesotho',
    'Nauruan': 'Nauru',
    'Nepalese': 'Nepal',
    'New Zealander': 'New Zealand',
    'Nicaraguan': 'Nicaragua',
    'Nigerian': 'Nigeria',
    'Nigerien': 'Niger',
    'North Korean': 'North Korea',
    'Norwegian': 'Norway',
    'Omani': 'Oman',
    'Pakistani': 'Pakistan',
    'Palauan': 'Palau',
    'Palestinian': 'Palestine',
    'Panamanian': 'Panama',
    'Papua New Guinean': 'Papua New Guinea',
    'Paraguayan': 'Paraguay',
    'Peruvian': 'Peru',
    'Polish': 'Poland',
    'Portuguese': 'Portugal',
    'Qatari': 'Qatar',
    'Romanian': 'Romania',
    'Russian': 'Russia',
    'Rwandan': 'Rwanda',
    'Salvadoran': 'El Salvador',
    'Sammarinese': 'San Marino',
    'Samoan': 'Samoa',
    'Sao Tomean': 'Sao Tome and Principe',
    'Saudi': 'Saudi Arabia',
    'Senegalese': 'Senegal',
    'Serbian': 'Serbia',
    'Seychellois': 'Seychelles',
    'Sierra Leonean': 'Sierra Leone',
    'Singaporean': 'Singapore',
    'Slovak': 'Slovakia',
    'Slovenian': 'Slovenia',
    'Solomon Islander': 'Solomon Islands',
    'Somali': 'Somalia',
    'South Korean': 'South Korea',
    'South Sudanese': 'South Sudan',
    'Spanish': 'Spain',
    'Sri Lankan': 'Sri Lanka',
    'St Lucian': 'Saint Lucia',
    'Sudanese': 'Sudan',
    'Surinamese': 'Suriname',
    'Swazi (Eswatini)': 'Eswatini',
    'Swedish': 'Sweden',
    'Swiss': 'Switzerland',
    'Syrian': 'Syria',
    'Taiwanese': 'Taiwan',
    'Tajik': 'Tajikistan',
    'Tanzanian': 'Tanzania',
    'Thai': 'Thailand',
    'Togolese': 'Togo',
    'Tongan': 'Tonga',
    'Trinidadian': 'Trinidad and Tobago',
    'Tunisian': 'Tunisia',
    'Turkish': 'Turkey',
    'Turkmen': 'Turkmenistan',
    'Tuvaluan': 'Tuvalu',
    'Ugandan': 'Uganda',
    'Ukrainian': 'Ukraine',
    'Uruguayan': 'Uruguay',
    'Uzbek': 'Uzbekistan',
    'Vanuatuan': 'Vanuatu',
    'Vatican': 'Vatican City',
    'Venezuelan': 'Venezuela',
    'Vietnamese': 'Vietnam',
    'Vincentian': 'Saint Vincent and the Grenadines',
    'Yemeni': 'Yemen',
}

# Countries in the same order as nationalities: common first, then A-Z.
# 'Dominica' shares the 'Dominican' demonym with the Dominican Republic, so it's added here.
COMMON_COUNTRIES = [COUNTRY_OF[n] for n in COMMON]
OTHER_COUNTRIES = sorted({COUNTRY_OF[n] for n in OTHERS} | {'Dominica'})
COUNTRIES = COMMON_COUNTRIES + OTHER_COUNTRIES

_CANONICAL_COUNTRY = {c.lower(): c for c in COUNTRIES}


def normalize_country(value: str) -> str:
    """Canonical spelling when it's on the list ('zimbabwe' -> 'Zimbabwe'); otherwise as typed."""
    text = ' '.join(str(value or '').split())
    return _CANONICAL_COUNTRY.get(text.lower(), text)
