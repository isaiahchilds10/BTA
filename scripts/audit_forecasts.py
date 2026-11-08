"""Developer-side, read-only calibration report. Never self-approves a model."""
import argparse,json
from pathlib import Path
from bta.models.validation import audit_chronological_forecasts


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('jsonl',type=Path)
    parser.add_argument('--sport',required=True)
    parser.add_argument('--market',required=True)
    parser.add_argument('--model-version',required=True)
    args=parser.parse_args()
    with args.jsonl.open(encoding='utf-8') as f:
        rows=[json.loads(x) for x in f if x.strip()]
    print(json.dumps(audit_chronological_forecasts(rows,sport=args.sport,
      market=args.market,model_version=args.model_version),indent=2,default=str))

if __name__=='__main__':main()
