#vocab.py

"""
Vocab lists for HM Land Registry data. Stores all UK counties, districts,
regions, property types, and postcode areas so that natural language
queries can be matched against known values.
"""


UK_COUNTIES = [
    "Bedfordshire", "Berkshire", "Bristol", "Buckinghamshire", "Cambridgeshire",
    "Cheshire", "City of London", "Cornwall", "Cumbria", "Derbyshire",
    "Devon", "Dorset", "Durham", "East Riding of Yorkshire", "East Sussex",
    "Essex", "Gloucestershire", "Greater London", "Greater Manchester",
    "Hampshire", "Herefordshire", "Hertfordshire", "Isle of Wight",
    "Kent", "Lancashire", "Leicestershire", "Lincolnshire", "Merseyside",
    "Norfolk", "North Yorkshire", "Northamptonshire", "Northumberland",
    "Nottinghamshire", "Oxfordshire", "Rutland", "Shropshire", "Somerset",
    "South Yorkshire", "Staffordshire", "Suffolk", "Surrey",
    "Tyne and Wear", "Warwickshire", "West Midlands", "West Sussex",
    "West Yorkshire", "Wiltshire", "Worcestershire",
    # Wales
    "Blaenau Gwent", "Bridgend", "Caerphilly", "Cardiff", "Carmarthenshire",
    "Ceredigion", "Conwy", "Denbighshire", "Flintshire", "Gwynedd",
    "Isle of Anglesey", "Merthyr Tydfil", "Monmouthshire", "Neath Port Talbot",
    "Newport", "Pembrokeshire", "Powys", "Rhondda Cynon Taf", "Swansea",
    "Torfaen", "Vale of Glamorgan", "Wrexham",
    # Scotland (council areas)
    "Aberdeen City", "Aberdeenshire", "Angus", "Argyll and Bute",
    "Clackmannanshire", "Dumfries and Galloway", "Dundee City", "East Ayrshire",
    "East Dunbartonshire", "East Lothian", "East Renfrewshire", "Edinburgh",
    "Falkirk", "Fife", "Glasgow", "Highland", "Inverclyde", "Midlothian",
    "Moray", "North Ayrshire", "North Lanarkshire", "Orkney Islands",
    "Perth and Kinross", "Renfrewshire", "Scottish Borders", "Shetland Islands",
    "South Ayrshire", "South Lanarkshire", "Stirling", "West Dunbartonshire",
    "West Lothian", "Western Isles",
    # Northern Ireland
    "Antrim and Newtownabbey", "Ards and North Down", "Armagh City, Banbridge and Craigavon",
    "Belfast", "Causeway Coast and Glens", "Derry and Strabane",
    "Fermanagh and Omagh", "Lisburn and Castlereagh", "Mid and East Antrim",
    "Mid Ulster", "Newry, Mourne and Down"
]

UK_DISTRICTS = [
    # --- ENGLAND: LONDON BOROUGHS ---
    "Barking and Dagenham", "Barnet", "Bexley", "Brent", "Bromley",
    "Camden", "Croydon", "Ealing", "Enfield", "Greenwich",
    "Hackney", "Hammersmith and Fulham", "Haringey", "Harrow",
    "Havering", "Hillingdon", "Hounslow", "Islington", "Kensington and Chelsea",
    "Kingston upon Thames", "Lambeth", "Lewisham", "Merton",
    "Newham", "Redbridge", "Richmond upon Thames", "Southwark",
    "Sutton", "Tower Hamlets", "Waltham Forest", "Wandsworth", "Westminster",

    # --- ENGLAND: METROPOLITAN BOROUGHS ---
    "Barnsley", "Birmingham", "Bolton", "Bradford", "Bury",
    "Calderdale", "Coventry", "Doncaster", "Dudley", "Gateshead",
    "Kirklees", "Knowsley", "Leeds", "Liverpool", "Manchester",
    "Newcastle upon Tyne", "North Tyneside", "Oldham", "Rochdale",
    "Rotherham", "Salford", "Sandwell", "Sefton", "Sheffield",
    "Solihull", "South Tyneside", "St Helens", "Stockport",
    "Sunderland", "Tameside", "Trafford", "Wakefield", "Walsall",
    "Wigan", "Wirral", "Wolverhampton",

    # --- ENGLAND: UNITARY AUTHORITIES ---
    "Bath and North East Somerset", "Bedford", "Blackburn with Darwen",
    "Blackpool", "Bournemouth, Christchurch and Poole", "Brighton and Hove",
    "Bristol", "Central Bedfordshire", "Cheshire East", "Cheshire West and Chester",
    "Cornwall", "Darlington", "Derby", "Dorset", "Durham",
    "East Riding of Yorkshire", "Halton", "Hartlepool", "Herefordshire",
    "Isle of Wight", "Kingston upon Hull", "Leicester", "Luton",
    "Medway", "Middlesbrough", "Milton Keynes", "North East Lincolnshire",
    "North Lincolnshire", "North Somerset", "Northumberland",
    "Nottingham", "Peterborough", "Plymouth", "Portsmouth",
    "Reading", "Redcar and Cleveland", "Rutland", "Slough",
    "Southampton", "Southend-on-Sea", "Stockton-on-Tees",
    "Stoke-on-Trent", "Swindon", "Telford and Wrekin",
    "Thurrock", "Torbay", "Warrington", "West Berkshire",
    "Wiltshire", "Windsor and Maidenhead", "Wokingham", "York",

    # --- ENGLAND: NON-METROPOLITAN DISTRICTS ---
    "Amber Valley", "Arun", "Ashfield", "Ashford", "Babergh",
    "Basildon", "Basingstoke and Deane", "Bassetlaw", "Blaby",
    "Bolsover", "Boston", "Braintree", "Breckland", "Brentwood",
    "Broadland", "Bromsgrove", "Broxbourne", "Broxtowe",
    "Burnley", "Cambridge", "Cannock Chase", "Canterbury",
    "Carlisle", "Castle Point", "Charnwood", "Chelmsford",
    "Cheltenham", "Cherwell", "Chesterfield", "Chichester",
    "Chorley", "Colchester", "Copeland", "Cotswold",
    "Crawley", "Dacorum", "Dartford", "Daventry",
    "Derbyshire Dales", "Dover", "East Cambridgeshire",
    "East Devon", "East Hampshire", "East Hertfordshire",
    "East Lindsey", "East Northamptonshire", "East Staffordshire",
    "East Suffolk", "Eastbourne", "Eastleigh", "Eden",
    "Elmbridge", "Epping Forest", "Epsom and Ewell",
    "Erewash", "Exeter", "Fareham", "Fenland",
    "Forest of Dean", "Fylde", "Gosport", "Gravesham",
    "Great Yarmouth", "Guildford", "Hambleton", "Harborough",
    "Harlow", "Harrogate", "Hastings", "Havant",
    "Hertsmere", "High Peak", "Horsham", "Huntingdonshire",
    "Hyndburn", "Ipswich", "Kettering", "Kings Lynn and West Norfolk",
    "Lancaster", "Lewes", "Lichfield", "Lincoln",
    "Maidstone", "Maldon", "Malvern Hills", "Mansfield",
    "Melton", "Mendip", "Mid Devon", "Mid Suffolk",
    "Mid Sussex", "Mole Valley", "New Forest", "Newark and Sherwood",
    "Newcastle-under-Lyme", "North Devon", "North East Derbyshire",
    "North Hertfordshire", "North Kesteven", "North Norfolk",
    "North Warwickshire", "North West Leicestershire",
    "Norwich", "Nuneaton and Bedworth", "Oadby and Wigston",
    "Oxford", "Pendle", "Preston", "Purbeck",
    "Redditch", "Reigate and Banstead", "Ribble Valley",
    "Richmondshire", "Rochford", "Rossendale", "Rugby",
    "Runnymede", "Rushcliffe", "Ryedale", "Scarborough",
    "Sedgemoor", "Sevenoaks", "Shepway", "South Cambridgeshire",
    "South Derbyshire", "South Hams", "South Holland",
    "South Kesteven", "South Lakeland", "South Norfolk",
    "South Oxfordshire", "South Ribble", "South Somerset",
    "South Staffordshire", "South Tyneside", "Spelthorne",
    "St Albans", "Stafford", "Staffordshire Moorlands",
    "Stevenage", "Stratford-on-Avon", "Stroud", "Suffolk Coastal",
    "Surrey Heath", "Swale", "Tamworth", "Tandridge",
    "Teignbridge", "Tendring", "Test Valley", "Tewkesbury",
    "Thanet", "Three Rivers", "Tonbridge and Malling",
    "Tunbridge Wells", "Uttlesford", "Vale of White Horse",
    "Warwick", "Watford", "Waverley", "Wealden",
    "Welwyn Hatfield", "West Devon", "West Lancashire",
    "West Lindsey", "West Oxfordshire", "West Suffolk",
    "Winchester", "Woking", "Worcester", "Worthing",
    "Wychavon", "Wycombe", "Wyre", "Wyre Forest",

    # --- SCOTLAND (32 Council Areas) ---
    "Aberdeen City", "Aberdeenshire", "Angus", "Argyll and Bute",
    "Clackmannanshire", "Dumfries and Galloway", "Dundee City",
    "East Ayrshire", "East Dunbartonshire", "East Lothian",
    "East Renfrewshire", "Edinburgh", "Falkirk", "Fife",
    "Glasgow", "Highland", "Inverclyde", "Midlothian",
    "Moray", "North Ayrshire", "North Lanarkshire",
    "Orkney Islands", "Perth and Kinross", "Renfrewshire",
    "Scottish Borders", "Shetland Islands", "South Ayrshire",
    "South Lanarkshire", "Stirling", "West Dunbartonshire",
    "West Lothian", "Western Isles",

    # --- WALES (22 Principal Areas) ---
    "Blaenau Gwent", "Bridgend", "Caerphilly", "Cardiff",
    "Carmarthenshire", "Ceredigion", "Conwy", "Denbighshire",
    "Flintshire", "Gwynedd", "Isle of Anglesey", "Merthyr Tydfil",
    "Monmouthshire", "Neath Port Talbot", "Newport",
    "Pembrokeshire", "Powys", "Rhondda Cynon Taf",
    "Swansea", "Torfaen", "Vale of Glamorgan", "Wrexham",

    # --- NORTHERN IRELAND (11 Districts) ---
    "Antrim and Newtownabbey", "Ards and North Down",
    "Armagh City, Banbridge and Craigavon", "Belfast",
    "Causeway Coast and Glens", "Derry and Strabane",
    "Fermanagh and Omagh", "Lisburn and Castlereagh",
    "Mid and East Antrim", "Mid Ulster",
    "Newry, Mourne and Down"
]

UK_REGIONS = {
    "North East": [
        "Northumberland", "Tyne and Wear", "Durham"
    ],
    "North West": [
        "Cheshire", "Cumbria", "Lancashire", "Greater Manchester", "Merseyside"
    ],
    "Yorkshire and the Humber": [
        "East Riding of Yorkshire", "North Yorkshire", "South Yorkshire", "West Yorkshire"
    ],
    "East Midlands": [
        "Derbyshire", "Leicestershire", "Lincolnshire", "Northamptonshire", 
        "Nottinghamshire", "Rutland"
    ],
    "West Midlands": [
        "Herefordshire", "Shropshire", "Staffordshire", "Warwickshire", 
        "West Midlands", "Worcestershire"
    ],
    "East of England": [
        "Bedfordshire", "Cambridgeshire", "Essex", "Hertfordshire", 
        "Norfolk", "Suffolk"
    ],
    "London": [
        "Greater London", "City of London"
    ],
    "South East": [
        "Berkshire", "Buckinghamshire", "East Sussex", "Hampshire", "Isle of Wight",
        "Kent", "Oxfordshire", "Surrey", "West Sussex"
    ],
    "South West": [
        "Bristol", "Cornwall", "Devon", "Dorset", "Gloucestershire", "Somerset", 
        "Wiltshire"
    ],
    "Wales": [
        "Blaenau Gwent", "Bridgend", "Caerphilly", "Cardiff", "Carmarthenshire",
        "Ceredigion", "Conwy", "Denbighshire", "Flintshire", "Gwynedd",
        "Isle of Anglesey", "Merthyr Tydfil", "Monmouthshire", "Neath Port Talbot",
        "Newport", "Pembrokeshire", "Powys", "Rhondda Cynon Taf", "Swansea",
        "Torfaen", "Vale of Glamorgan", "Wrexham"
    ],
    "Scotland": [
        "Aberdeen City", "Aberdeenshire", "Angus", "Argyll and Bute",
        "Clackmannanshire", "Dumfries and Galloway", "Dundee City", "East Ayrshire",
        "East Dunbartonshire", "East Lothian", "East Renfrewshire", "Edinburgh",
        "Falkirk", "Fife", "Glasgow", "Highland", "Inverclyde", "Midlothian",
        "Moray", "North Ayrshire", "North Lanarkshire", "Orkney Islands",
        "Perth and Kinross", "Renfrewshire", "Scottish Borders", "Shetland Islands",
        "South Ayrshire", "South Lanarkshire", "Stirling", "West Dunbartonshire",
        "West Lothian", "Western Isles"
    ],
    "Northern Ireland": [
        "Antrim and Newtownabbey", "Ards and North Down", "Armagh City, Banbridge and Craigavon",
        "Belfast", "Causeway Coast and Glens", "Derry and Strabane",
        "Fermanagh and Omagh", "Lisburn and Castlereagh", "Mid and East Antrim",
        "Mid Ulster", "Newry, Mourne and Down"
    ]
}

UK_PROPERTY_TYPES = [
    "detached",
    "semi-detached",
    "terraced",
    "flat",
    "other",
]

UK_POSTCODE_AREAS = [
    "AB", "AL", "B", "BA", "BB", "BD", "BH", "BL", "BN", "BR", "BS", "BT",
    "CA", "CB", "CF", "CH", "CM", "CO", "CR", "CT", "CV", "CW", "DA", "DD",
    "DE", "DG", "DH", "DL", "DN", "DT", "DY", "E", "EC", "EH", "EN", "EX",
    "FK", "FY", "G", "GL", "GU", "GY", "HA", "HD", "HG", "HP", "HR", "HS",
    "HU", "HX", "IG", "IM", "IP", "IV", "JE", "KA", "KT", "KW", "KY", "L",
    "LA", "LD", "LE", "LL", "LN", "LS", "LU", "M", "ME", "MK", "ML", "N",
    "NE", "NG", "NN", "NP", "NR", "NW", "OL", "OX", "PA", "PE", "PH", "PL",
    "PO", "PR", "RG", "RH", "RM", "S", "SA", "SE", "SG", "SK", "SL", "SM",
    "SN", "SO", "SP", "SR", "SS", "ST", "SW", "SY", "TA", "TD", "TF", "TN",
    "TQ", "TR", "TS", "TW", "UB", "W", "WA", "WC", "WD", "WF", "WN", "WR",
    "WS", "WV", "YO", "ZE"
]
