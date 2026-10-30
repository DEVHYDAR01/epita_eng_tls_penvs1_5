# scripts/debug_challenge.py
"""
EPITA CM2 Debugging Challenge: API Payload & Batch Aggregator.
This script contains runtime type mismatches and faulty aggregations.
DO NOT USE print()! Use your interactive debugger.
"""

def parse_api_record(raw_entry: str) -> dict:
    # Simulates records: "record_id,entity_name,raw_volume,status,weight_multiplier"
    parts = raw_entry.strip().split(",")
    return {
        "id": parts[0],
        "entity": parts[1],
        "volume": float(parts[2]),
        "status": parts[3],
        "weight": float(parts[4])
    }

def compute_weighted_metric(volume, weight):
    return volume * weight

def aggregate_telemetry(payload: list[str]) -> dict:
    total_volume = 0
    successful_entries = 0
    high_impact_count = 0

    for idx, row in enumerate(payload):
        record = parse_api_record(row)

        if record["status"] == "SUCCESS":
            # Set a conditional breakpoint here when idx == 2
            impact = compute_weighted_metric(record["volume"], record["weight"])

            if impact > 500:
                high_impact_count += 1

            total_volume += record["volume"]
            successful_entries += 1

    avg_volume = total_volume / successful_entries if successful_entries > 0 else 0
    return {
        "successful_entries": successful_entries,
        "total_volume": total_volume,
        "avg_volume": avg_volume,
        "high_impact_count": high_impact_count
    }

if __name__ == "__main__":
    api_payload = [
        "REC_001,service_alpha,120,SUCCESS,2",
        "REC_002,service_beta,0,FAILURE,1",
        "REC_003,service_gamma,450,SUCCESS,3",
        "REC_004,service_delta,80,SUCCESS,1",
        "REC_005,service_epsilon,1500,PENDING,4"
    ]

    # Expected output for SUCCESS records (REC_001, REC_003, REC_004):
    # - total_volume: 120 + 450 + 80 = 650.0
    # - avg_volume: 650 / 3 = 216.67
    # - high_impact_count (impact > 500):
    #     REC_001: 120 * 2 = 240
    #     REC_003: 450 * 3 = 1350 (>500)
    #     REC_004: 80 * 1 = 80
    #     Total high impact = 1

    result = aggregate_telemetry(api_payload)
    print("Aggregate Result:", result)
