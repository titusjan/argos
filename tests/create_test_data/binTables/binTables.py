import polars  as pl

def main():
    df = pl.DataFrame({
        "a": [1, 2, 3],
        "b": ["x", "y", "z"],
        "d": [1.0, 2.0, 3.0],
    })
    df.write_parquet("example1.parquet")
    df.write_ipc("example1.ipc")
    df = df.with_columns(pl.col("b").cast(pl.Categorical))
    df.write_parquet("example2.parquet")
    df.write_ipc("example2.ipc")

if __name__ == "__main__":
    main()
    
    