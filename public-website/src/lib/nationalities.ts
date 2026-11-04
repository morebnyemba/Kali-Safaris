// Nationalities offered in the traveller forms. Copy of
// whatsappcrm_backend/customer_data/nationalities.py (the master list);
// customer_data/test_nationalities.py fails if the two drift apart.

/** Zimbabwe, our SADC neighbours, then the main overseas markets. */
export const COMMON_NATIONALITIES: string[] = [
  'Zimbabwean', 'South African', 'Zambian', 'Botswanan', 'Namibian', 'Mozambican', 'Malawian',
  'British', 'American', 'German',
];

/** Everything else, A–Z. */
export const OTHER_NATIONALITIES: string[] = [
  'Afghan', 'Albanian', 'Algerian', 'Andorran', 'Angolan', 'Antiguan', 'Argentine', 'Armenian',
  'Australian', 'Austrian', 'Azerbaijani', 'Bahamian', 'Bahraini', 'Bangladeshi', 'Barbadian',
  'Belarusian', 'Belgian', 'Belizean', 'Beninese', 'Bhutanese', 'Bolivian', 'Bosnian', 'Brazilian',
  'Bruneian', 'Bulgarian', 'Burkinabe', 'Burmese', 'Burundian', 'Cambodian', 'Cameroonian',
  'Canadian', 'Cape Verdean', 'Central African', 'Chadian', 'Chilean', 'Chinese', 'Colombian',
  'Comoran', 'Congolese (Congo)', 'Congolese (DRC)', 'Costa Rican', 'Croatian', 'Cuban', 'Cypriot',
  'Czech', 'Danish', 'Djiboutian', 'Dominican', 'Dutch', 'East Timorese', 'Ecuadorian', 'Egyptian',
  'Emirati', 'Equatorial Guinean', 'Eritrean', 'Estonian', 'Ethiopian', 'Fijian', 'Filipino',
  'Finnish', 'French', 'Gabonese', 'Gambian', 'Georgian', 'Ghanaian', 'Greek', 'Grenadian',
  'Guatemalan', 'Guinea-Bissauan', 'Guinean', 'Guyanese', 'Haitian', 'Honduran', 'Hong Konger',
  'Hungarian', 'I-Kiribati', 'Icelandic', 'Indian', 'Indonesian', 'Iranian', 'Iraqi', 'Irish',
  'Israeli', 'Italian', 'Ivorian', 'Jamaican', 'Japanese', 'Jordanian', 'Kazakh', 'Kenyan',
  'Kittitian', 'Kosovan', 'Kuwaiti', 'Kyrgyz', 'Lao', 'Latvian', 'Lebanese', 'Liberian', 'Libyan',
  'Liechtensteiner', 'Lithuanian', 'Luxembourger', 'Macedonian', 'Malagasy', 'Malaysian',
  'Maldivian', 'Malian', 'Maltese', 'Marshallese', 'Mauritanian', 'Mauritian', 'Mexican',
  'Micronesian', 'Moldovan', 'Monegasque', 'Mongolian', 'Montenegrin', 'Moroccan',
  'Mosotho (Lesotho)', 'Nauruan', 'Nepalese', 'New Zealander', 'Nicaraguan', 'Nigerian',
  'Nigerien', 'North Korean', 'Norwegian', 'Omani', 'Pakistani', 'Palauan', 'Palestinian',
  'Panamanian', 'Papua New Guinean', 'Paraguayan', 'Peruvian', 'Polish', 'Portuguese', 'Qatari',
  'Romanian', 'Russian', 'Rwandan', 'Salvadoran', 'Sammarinese', 'Samoan', 'Sao Tomean', 'Saudi',
  'Senegalese', 'Serbian', 'Seychellois', 'Sierra Leonean', 'Singaporean', 'Slovak', 'Slovenian',
  'Solomon Islander', 'Somali', 'South Korean', 'South Sudanese', 'Spanish', 'Sri Lankan',
  'St Lucian', 'Sudanese', 'Surinamese', 'Swazi (Eswatini)', 'Swedish', 'Swiss', 'Syrian',
  'Taiwanese', 'Tajik', 'Tanzanian', 'Thai', 'Togolese', 'Tongan', 'Trinidadian', 'Tunisian',
  'Turkish', 'Turkmen', 'Tuvaluan', 'Ugandan', 'Ukrainian', 'Uruguayan', 'Uzbek', 'Vanuatuan',
  'Vatican', 'Venezuelan', 'Vietnamese', 'Vincentian', 'Yemeni',
];

export const ALL_NATIONALITIES: string[] = [...COMMON_NATIONALITIES, ...OTHER_NATIONALITIES];
