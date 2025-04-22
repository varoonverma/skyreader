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
                "message_identify": "102327",
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
                    "arrival_day": "10"
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
                "message_identify": "102029",
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
                    "arrival_day": "31"
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
                "message_identify": "102133",
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
                    "departure_day": "25"
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
                "message_identify": "102147",
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
                    "departure_day": "20"
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
                "message_identify": "102333",
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
                    "departure_day": "22"
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
        }
    ]