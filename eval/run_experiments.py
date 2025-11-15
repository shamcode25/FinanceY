"""
Evaluation script for QA endpoint
"""
import json
import time
import requests
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any


# API base URL
API_BASE_URL = "http://localhost:8000"


def load_dataset(dataset_path: str = "eval/dataset.json") -> List[Dict[str, Any]]:
    """Load evaluation dataset"""
    path = Path(dataset_path)
    if not path.exists():
        raise FileNotFoundError(f"Dataset not found: {dataset_path}")
    
    with open(path, "r") as f:
        dataset = json.load(f)
    
    return dataset


def check_keywords(answer: str, expected_keywords: List[str]) -> int:
    """Check how many expected keywords appear in the answer"""
    answer_lower = answer.lower()
    hits = 0
    
    for keyword in expected_keywords:
        if keyword.lower() in answer_lower:
            hits += 1
    
    return hits


def evaluate_qa_endpoint(
    ticker: str,
    filing_type: str,
    year: int,
    question: str,
    top_k: int = 5,
    timeout: int = 30
) -> Dict[str, Any]:
    """Evaluate QA endpoint for a single question"""
    start_time = time.time()
    
    try:
        # Make API request
        response = requests.post(
            f"{API_BASE_URL}/qa",
            json={
                "ticker": ticker,
                "filing_type": filing_type,
                "year": year,
                "question": question,
                "top_k": top_k
            },
            timeout=timeout
        )
        
        # Calculate latency
        latency_ms = (time.time() - start_time) * 1000
        
        if response.status_code == 200:
            data = response.json()
            answer = data.get("answer", "")
            sources = data.get("sources", [])
            
            return {
                "success": True,
                "answer": answer,
                "sources": sources,
                "latency_ms": latency_ms,
                "status_code": response.status_code
            }
        else:
            return {
                "success": False,
                "answer": "",
                "sources": [],
                "latency_ms": latency_ms,
                "status_code": response.status_code,
                "error": response.text
            }
    except Exception as e:
        latency_ms = (time.time() - start_time) * 1000
        return {
            "success": False,
            "answer": "",
            "sources": [],
            "latency_ms": latency_ms,
            "status_code": 0,
            "error": str(e)
        }


def run_experiments(
    dataset: List[Dict[str, Any]],
    configs: List[Dict[str, Any]],
    output_path: str = "eval/results.csv"
) -> pd.DataFrame:
    """Run experiments with different configurations"""
    results = []
    
    for config in configs:
        config_name = config.get("name", "default")
        top_k = config.get("top_k", 5)
        
        print(f"\nRunning experiments with config: {config_name} (top_k={top_k})")
        
        for item in dataset:
            ticker = item["ticker"]
            filing_type = item["filing_type"]
            year = item["year"]
            question = item["question"]
            expected_keywords = item.get("expected_keywords", [])
            
            print(f"  Evaluating: {ticker} {filing_type} {year} - {question[:50]}...")
            
            # Evaluate QA endpoint
            result = evaluate_qa_endpoint(
                ticker=ticker,
                filing_type=filing_type,
                year=year,
                question=question,
                top_k=top_k
            )
            
            # Check keyword hits
            num_keywords_hit = 0
            if result["success"]:
                num_keywords_hit = check_keywords(result["answer"], expected_keywords)
            
            # Store result
            results.append({
                "config_name": config_name,
                "ticker": ticker,
                "filing_type": filing_type,
                "year": year,
                "question": question,
                "expected_keywords": ", ".join(expected_keywords),
                "answer": result["answer"],
                "sources": ", ".join(result["sources"]),
                "latency_ms": result["latency_ms"],
                "num_keywords_hit": num_keywords_hit,
                "total_keywords": len(expected_keywords),
                "success": result["success"],
                "status_code": result["status_code"],
                "error": result.get("error", "")
            })
    
    # Create DataFrame
    df = pd.DataFrame(results)
    
    # Save to CSV
    output_path_obj = Path(output_path)
    output_path_obj.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path_obj, index=False)
    
    return df


def compute_metrics(df: pd.DataFrame) -> Dict[str, float]:
    """Compute evaluation metrics"""
    metrics = {}
    
    # Overall metrics
    metrics["total_questions"] = len(df)
    metrics["successful_requests"] = df["success"].sum()
    metrics["success_rate"] = df["success"].mean()
    
    # Keyword hit rate
    metrics["avg_keywords_hit"] = df["num_keywords_hit"].mean()
    metrics["avg_keyword_hit_rate"] = (df["num_keywords_hit"] / df["total_keywords"]).mean()
    
    # Latency
    metrics["avg_latency_ms"] = df["latency_ms"].mean()
    metrics["median_latency_ms"] = df["latency_ms"].median()
    metrics["p95_latency_ms"] = df["latency_ms"].quantile(0.95)
    metrics["p99_latency_ms"] = df["latency_ms"].quantile(0.99)
    
    # Per-config metrics
    if "config_name" in df.columns:
        config_metrics = {}
        for config_name in df["config_name"].unique():
            config_df = df[df["config_name"] == config_name]
            config_metrics[config_name] = {
                "success_rate": config_df["success"].mean(),
                "avg_keywords_hit": config_df["num_keywords_hit"].mean(),
                "avg_keyword_hit_rate": (config_df["num_keywords_hit"] / config_df["total_keywords"]).mean(),
                "avg_latency_ms": config_df["latency_ms"].mean()
            }
        metrics["per_config"] = config_metrics
    
    return metrics


def main():
    """Main evaluation function"""
    print("Loading dataset...")
    dataset = load_dataset()
    print(f"Loaded {len(dataset)} questions")
    
    # Define configurations to test
    configs = [
        {"name": "top_k_3", "top_k": 3},
        {"name": "top_k_5", "top_k": 5},
        {"name": "top_k_10", "top_k": 10}
    ]
    
    print(f"\nRunning experiments with {len(configs)} configurations...")
    df = run_experiments(dataset, configs)
    
    print(f"\nResults saved to: eval/results.csv")
    print(f"Total results: {len(df)}")
    
    # Compute metrics
    print("\nComputing metrics...")
    metrics = compute_metrics(df)
    
    # Print metrics
    print("\n=== Evaluation Metrics ===")
    print(f"Total questions: {metrics['total_questions']}")
    print(f"Successful requests: {metrics['successful_requests']}")
    print(f"Success rate: {metrics['success_rate']:.2%}")
    print(f"Avg keywords hit: {metrics['avg_keywords_hit']:.2f}")
    print(f"Avg keyword hit rate: {metrics['avg_keyword_hit_rate']:.2%}")
    print(f"Avg latency: {metrics['avg_latency_ms']:.2f} ms")
    print(f"Median latency: {metrics['median_latency_ms']:.2f} ms")
    print(f"P95 latency: {metrics['p95_latency_ms']:.2f} ms")
    print(f"P99 latency: {metrics['p99_latency_ms']:.2f} ms")
    
    # Print per-config metrics
    if "per_config" in metrics:
        print("\n=== Per-Config Metrics ===")
        for config_name, config_metrics in metrics["per_config"].items():
            print(f"\n{config_name}:")
            print(f"  Success rate: {config_metrics['success_rate']:.2%}")
            print(f"  Avg keywords hit: {config_metrics['avg_keywords_hit']:.2f}")
            print(f"  Avg keyword hit rate: {config_metrics['avg_keyword_hit_rate']:.2%}")
            print(f"  Avg latency: {config_metrics['avg_latency_ms']:.2f} ms")
    
    # Save metrics to JSON
    metrics_path = Path("eval/metrics.json")
    metrics_path.parent.mkdir(parents=True, exist_ok=True)
    with open(metrics_path, "w") as f:
        json.dump(metrics, f, indent=2)
    
    print(f"\nMetrics saved to: eval/metrics.json")


if __name__ == "__main__":
    main()
