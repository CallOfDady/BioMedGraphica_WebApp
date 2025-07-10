import argparse
import json
import sys
from backend.processors import process

def main():
    parser = argparse.ArgumentParser(description="Batch process omics entity files.")
    parser.add_argument("--config", type=str, required=True, help="Path to the JSON config file")
    parser.add_argument("--database_path", type=str, required=True, help="Path to the database directory")
    parser.add_argument("--output_dir", type=str, required=True, help="Path to the output directory")

    args = parser.parse_args()

    try:
        # Load configuration
        with open(args.config, "r", encoding="utf-8") as f:
            config_data = json.load(f)

        if not isinstance(config_data, dict) or "configs" not in config_data:
            raise ValueError("Config JSON must be an object containing a 'configs' list.")

        configs = config_data["configs"]
        finalize_cfg = config_data.get("finalize", {})

        # Call processing pipeline
        result = process(
            *configs,
            database_path=args.database_path,
            output_dir=args.output_dir,
            file_order=finalize_cfg.get("file_order"),
            apply_zscore=finalize_cfg.get("apply_zscore", False),
            edge_types=finalize_cfg.get("edge_types"),
        )

        # Print summary
        print("\n✅ Processing completed.")
        print(f"→ Common sample IDs: {len(result['common_sample_ids'])}")
        print(f"→ Summary: {result['summary']['success']} succeeded, {result['summary']['error']} failed\n")

        for r in result["results"]:
            status = "✅" if r["status"] == "success" else "❌"
            print(f"{status} {r['feature_label']}: {r['status']}")
            if r["status"] == "error":
                print(f"   ↳ Error: {r['error']}")

        finalized = result.get("finalized_dataset", {})
        if finalized.get("status") == "success":
            print("\n📦 Finalized dataset saved to:", finalized.get("processed_data_path"))
            print("🧩 Edge types included:", finalized.get("selected_edge_types"))
        else:
            print("\n⚠️ Finalization failed:", finalized.get("error", "Unknown error"))

    except Exception as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
