"""
Few-shot examples for TTY message parsing.
"""
from typing import List, Dict


def load_few_shot_examples() -> List[Dict]:
    """
    Load few-shot examples for TTY message parsing.

    Returns:
        List of dictionaries containing example messages and their parsed JSON
    """
    return [
        {
            "message": "QU HDQOOQF\n.QXSXMXS 102327\nA81\nFI JST0430/AN VH-VGR\nDT QXS OOL1 102327 M44A\n-\nMVA\nJST0430/10.VHVGR.OOL\nAA2327",
            "parsed_json": {
                "priority_code": "QU",
                "destination_address": ["HDQOOQF"],
                "origin_address": "QXSXMXS",
                "message_identity": "102327",
                "report_indicator": "A81",
                "flight_identification_message": {
                    "airline_iata": "JST",
                    "flight_number": "0430",
                    "registration": "VH-VGR"
                },
                "communication_service_information": "DT QXS OOL1 102327 M44A",
                "standard_message_id": "MVA",
                "flight_identifier": {
                    "airline_iata": "JST",
                    "flight_number": "0430",
                    "registration": "VHVGR",
                    "movement_day": "10"
                },
                "movement_info": {
                    "type": "AA",
                    "movement": "Arrival",
                    "wheels_on_time": "23:27",
                    "arrival_airport_iata": "OOL"
                }
            }
        },
        {
            "message": "QU HDQOOQF\n.QXSXMXS 102029\nA81\nFI JST0430/AN VH-ABC\nDT QXS MEL1 102029 M20A\n-\nMVA\nJST0430/31.VHABC.SYD\nAA2020/2027\nSI FB  69",
            "parsed_json": {
                "priority_code": "QU",
                "destination_address": ["HDQOOQF"],
                "origin_address": "QXSXMXS",
                "message_identity": "102029",
                "report_indicator": "A81",
                "flight_identification_message": {
                    "airline_iata": "JST",
                    "flight_number": "0430",
                    "registration": "VH-ABC"
                },
                "communication_service_information": "DT QXS MEL1 102029 M20A",
                "standard_message_id": "MVA",
                "flight_identifier": {
                    "airline_iata": "JST",
                    "flight_number": "0430",
                    "registration": "VHABC",
                    "movement_day": "31"
                },
                "movement_info": {
                    "type": "AA",
                    "movement": "Arrival",
                    "wheels_on_time": "20:20",
                    "blocks_on_time": "20:27",
                    "arrival_airport_iata": "SYD"
                },
                "supplementary_info": "SI FB 69"
            }
        },
        {
            "message": "QU HDQOOQF\n.QXSXMXS 102133\nA80\nFI JQ0399/AN BN-LFM\nDT QXS MEL1 102133 M27A\n-\nMVA\nJQ0399/25.BNLFM.MEL\nAD2133 OOL\nSI FB  97",
            "parsed_json": {
                "priority_code": "QU",
                "destination_address": ["HDQOOQF"],
                "origin_address": "QXSXMXS",
                "message_identity": "102133",
                "report_indicator": "A80",
                "flight_identification_message": {
                    "airline_iata": "JQ",
                    "flight_number": "0399",
                    "registration": "BN-LFM"
                },
                "communication_service_information": "DT QXS MEL1 102133 M27A",
                "standard_message_id": "MVA",
                "flight_identifier": {
                    "airline_iata": "JQ",
                    "flight_number": "0399",
                    "registration": "BNLFM",
                    "movement_day": "25"
                },
                "movement_info": {
                    "type": "AD",
                    "movement": "Departure",
                    "blocks_off_time": "21:33",
                    "departure_airport_iata": "MEL",
                    "arrival_airport_iata": "OOL"
                },
                "supplementary_info": "SI FB 97"
            }
        },
        {
            "message": "QU HDQOOQF\n.QXSXMXS 102147\nA80\nFI JQ3123/AN AO-TGR\nDT QXS MEL1 102147 M31A\n-\nMVA\nJQ3123/20.AOTGR.MEL\nAD2133/2147 EA2328 OOL",
            "parsed_json": {
                "priority_code": "QU",
                "destination_address": ["HDQOOQF"],
                "origin_address": "QXSXMXS",
                "message_identity": "102147",
                "report_indicator": "A80",
                "flight_identification_message": {
                    "airline_iata": "JQ",
                    "flight_number": "3123",
                    "registration": "AO-TGR"
                },
                "communication_service_information": "DT QXS MEL1 102147 M31A",
                "standard_message_id": "MVA",
                "flight_identifier": {
                    "airline_iata": "JQ",
                    "flight_number": "3123",
                    "registration": "AOTGR",
                    "movement_day": "20"
                },
                "movement_info": {
                    "type": "AD",
                    "movement": "Departure",
                    "blocks_off_time": "21:33",
                    "wheels_off_time": "21:47",
                    "estimated_arrival_time": "23:28",
                    "departure_airport_iata": "MEL",
                    "arrival_airport_iata": "OOL"
                }
            }
        },
        {
            "message": "QU HDQOOQF\n.QXSXMXS 102333\nA80\nFI QFA5880/AN VI-RGV\nDT QXS OOL1 102333 M46A\n-\nMVA\nQFA5880/22.VIRGV.PER\nAD2327/2330\nSI FB  50",
            "parsed_json": {
                "priority_code": "QU",
                "destination_address": ["HDQOOQF"],
                "origin_address": "QXSXMXS",
                "message_identity": "102333",
                "report_indicator": "A80",
                "flight_identification_message": {
                    "airline_iata": "QFA",
                    "flight_number": "5880",
                    "registration": "VI-RGV"
                },
                "communication_service_information": "DT QXS OOL1 102333 M46A",
                "standard_message_id": "MVA",
                "flight_identifier": {
                    "airline_iata": "QFA",
                    "flight_number": "5880",
                    "registration": "VIRGV",
                    "movement_day": "22"
                },
                "movement_info": {
                    "type": "AD",
                    "movement": "Departure",
                    "blocks_off_time": "23:27",
                    "wheels_off_time": "23:30",
                    "departure_airport_iata": "PER"
                },
                "supplementary_info": "SI FB 50"
            }
        },
        {
            "message": "QU HDQWWQF\n.SYDWWQF 110906\nMVT\nQFA2915/11DEC243 .VHNHY.BQB\nEA0905\nSI FILD /",
            "parsed_json": {
                "priority_code": "QU",
                "destination_address": ["HDQWWQF"],
                "origin_address": "SYDWWQF",
                "message_identity": "110906",
                "standard_message_id": "MVT",
                "flight_identifier": {
                    "airline_iata": "QFA",
                    "flight_number": "2915",
                    "registration": "VHNHY",
                    "movement_day": "11"
                },
                "movement_info": {
                    "type": "EA",
                    "movement": "EstimatedArrival",
                    "estimated_arrival_time": "09:05",
                    "arrival_airport_iata": "BQB"
                },
                "supplementary_info": "SI FILD /"
            }
        },
        {
            "message" : "QU HDQWWQF\n.SYDWWQF 170305\nMVT\nQFA2913/17DEC242 .VHNHY.BQB\nEA0245\nSI FILD /",
            "parsed_json" : {
                "priority_code" : "QU",
                "destination_address" : [ "HDQWWQF" ],
                "origin_address" : "SYDWWQF",
                "message_identity" : "170305",
                "standard_message_id" : "MVT",
                "flight_identifier" : {
                    "airline_iata" : "QFA",
                    "flight_number" : "2913",
                    "registration" : "VHNHY",
                    "movement_day" : "17"
                },
                "movement_info" : {
                    "type" : "EA",
                    "movement" : "EstimatedArrival",
                    "estimated_arrival_time" : "02:45",
                    "arrival_airport_iata" : "BQB"
                },
                "supplementary_info": "SI FILD /"
            }
        },
        {
            "message" : "QU HDQWWQF\n.SYDWWQF 240610\nMVT\nQFA2913/24DEC242 .VHVQQ.BQB\nEA0615\nSI FILD /",
            "parsed_json" : {
                "priority_code" : "QU",
                "destination_address" : [ "HDQWWQF" ],
                "origin_address" : "SYDWWQF",
                "message_identity" : "240610",
                "standard_message_id" : "MVT",
                "flight_identifier" : {
                    "airline_iata" : "QFA",
                    "flight_number" : "2913",
                    "registration" : "VHVQQ",
                    "movement_day" : "24"
                },
                "movement_info" : {
                    "type" : "EA",
                    "movement" : "EstimatedArrival",
                    "estimated_arrival_time" : "06:15",
                    "arrival_airport_iata" : "BQB"
                },
                "supplementary_info": "SI FILD /"
            }
        },
        {
            "message" : "QU HDQWWQF\n.HDQRMAA 261642\nMVT\nAA2911/26.XXXXX.AUS\nEA1723",
            "parsed_json" : {
                "priority_code" : "QU",
                "destination_address" : [ "HDQWWQF" ],
                "origin_address" : "HDQRMAA",
                "message_identity" : "261642",
                "standard_message_id" : "MVT",
                "flight_identifier" : {
                    "airline_iata" : "AA",
                    "flight_number" : "2911",
                    "registration" : "XXXXX",
                    "movement_day" : "26"
                },
                "movement_info" : {
                    "type" : "EA",
                    "movement" : "EstimatedArrival",
                    "estimated_arrival_time" : "17:23",
                    "arrival_airport_iata" : "AUS"
                }
            }
        },
        {
            "message" : "QU HDQWWQF\n.HDQRMAA 261642\nMVT\nAA2949/26.XXXXX.MIA\nEA1739",
            "parsed_json" : {
                "priority_code" : "QU",
                "destination_address" : [ "HDQWWQF" ],
                "origin_address" : "HDQRMAA",
                "message_identity" : "261642",
                "standard_message_id" : "MVT",
                "flight_identifier" : {
                    "airline_iata" : "AA",
                    "flight_number" : "2949",
                    "registration" : "XXXXX",
                    "movement_day" : "26"
                },
                "movement_info" : {
                    "type" : "EA",
                    "movement" : "EstimatedArrival",
                    "estimated_arrival_time" : "17:23",
                    "arrival_airport_iata" : "MIA"
                }
            }
        },
        {
            "message" : "QU HDQWWQF\n.SYDWWQF 120547\nMVA\nQF1620/12DEC24.VH8NZ  .PER\nAD0536/0547 EA0715 PBO\nSI UNIQUE ID OF ORIGINAL ACARS MESSAGE: LLHX224",
            "parsed_json" : {
                "priority_code" : "QU",
                "destination_address" : [ "HDQWWQF" ],
                "origin_address" : "SYDWWQF",
                "message_identity" : "120547",
                "standard_message_id" : "MVA",
                "flight_identifier" : {
                    "airline_iata" : "QF",
                    "flight_number" : "1620",
                    "registration" : "VH8NZ  ",
                    "movement_day" : "12"
                },
                "movement_info" : {
                    "type" : "AD",
                    "movement" : "Departure",
                    "blocks_off_time" : "05:36",
                    "wheels_off_time" : "05:47",
                    "estimated_arrival_time" : "07:15",
                    "departure_airport_iata" : "PER",
                    "arrival_airport_iata" : "PBO"
                },
                "supplementary_info": "SI UNIQUE ID OF ORIGINAL ACARS MESSAGE: LLHX224"
            }
        },
        {
            "message" : "QU HDQWWQF\n.SYDWWQF 160406\nMVA\nQF1727/16DEC24.VH8NR  .KTA\nAD0359/0405 EA0600 PER\nSI UNIQUE ID OF ORIGINAL ACARS MESSAGE: LPHG324",
            "parsed_json" : {
                "priority_code" : "QU",
                "destination_address" : [ "HDQWWQF" ],
                "origin_address" : "SYDWWQF",
                "message_identity" : "160406",
                "standard_message_id" : "MVA",
                "flight_identifier" : {
                    "airline_iata" : "QF",
                    "flight_number" : "1727",
                    "registration" : "VH8NR  ",
                    "movement_day" : "16"
                },
                "movement_info" : {
                    "type" : "AD",
                    "movement" : "Departure",
                    "blocks_off_time" : "03:59",
                    "wheels_off_time" : "04:05",
                    "estimated_arrival_time" : "06:00",
                    "departure_airport_iata" : "KTA",
                    "arrival_airport_iata" : "PER"
                },
                "supplementary_info": "SI UNIQUE ID OF ORIGINAL ACARS MESSAGE: LPHG324"
            }
        },
        {
            "message" : "QU HDQWWQF\n.SYDWWQF 170138\nMVA\nQF2763/16DEC24.VHJQG  .GYB\nAD0121/0130 EA0314 PER\nSI UNIQUE ID OF ORIGINAL ACARS MESSAGE: LQFU914",
            "parsed_json" : {
                "priority_code" : "QU",
                "destination_address" : [ "HDQWWQF" ],
                "origin_address" : "SYDWWQF",
                "message_identity" : "170138",
                "standard_message_id" : "MVA",
                "flight_identifier" : {
                    "airline_iata" : "QF",
                    "flight_number" : "2763",
                    "registration" : "VHJQG  ",
                    "movement_day" : "16"
                },
                "movement_info" : {
                    "type" : "AD",
                    "movement" : "Departure",
                    "blocks_off_time" : "01:21",
                    "wheels_off_time" : "01:30",
                    "estimated_arrival_time" : "03:14",
                    "departure_airport_iata" : "GYB",
                    "arrival_airport_iata" : "PER"
                },
                "supplementary_info": "SI UNIQUE ID OF ORIGINAL ACARS MESSAGE: LQFU914"
            }
        },
        {
            "message" : "QU HDQWWQF\n.SYDWWQF 200035\nMVA\nQF2957/20DEC24.VHVQP  .OCM\nAD0024/0028 EA0157 PER\nSI UNIQUE ID OF ORIGINAL ACARS MESSAGE: LTFL574",
            "parsed_json" : {
                "priority_code" : "QU",
                "destination_address" : [ "HDQWWQF" ],
                "origin_address" : "SYDWWQF",
                "message_identity" : "200035",
                "standard_message_id" : "MVA",
                "flight_identifier" : {
                    "airline_iata" : "QF",
                    "flight_number" : "2957",
                    "registration" : "VHVQP  ",
                    "movement_day" : "20"
                },
                "movement_info" : {
                    "type" : "AD",
                    "movement" : "Departure",
                    "blocks_off_time" : "00:24",
                    "wheels_off_time" : "00:28",
                    "estimated_arrival_time" : "01:57",
                    "departure_airport_iata" : "OCM",
                    "arrival_airport_iata" : "PER"
                },
                "supplementary_info": "SI UNIQUE ID OF ORIGINAL ACARS MESSAGE: LTFL574"
            }
        },
        {
            "message" : "QU HDQWWQF\n.SYDWWQF 262338\nMVA\nQF1652/26DEC24.VH8NZ  .PER\nAD2324/2338 EA0147 BME\nSI UNIQUE ID OF ORIGINAL ACARS MESSAGE: L1ER354",
            "parsed_json" : {
                "priority_code" : "QU",
                "destination_address" : [ "HDQWWQF" ],
                "origin_address" : "SYDWWQF",
                "message_identity" : "262338",
                "standard_message_id" : "MVA",
                "flight_identifier" : {
                    "airline_iata" : "QF",
                    "flight_number" : "1652",
                    "registration" : "VH8NZ  ",
                    "movement_day" : "26"
                },
                "movement_info" : {
                    "type" : "AD",
                    "movement" : "Departure",
                    "blocks_off_time" : "23:24",
                    "wheels_off_time" : "23:30",
                    "estimated_arrival_time" : "01:47",
                    "departure_airport_iata" : "PER",
                    "arrival_airport_iata" : "BME"
                },
                "supplementary_info": "SI UNIQUE ID OF ORIGINAL ACARS MESSAGE: L1ER354"
            }
        }
    ]
