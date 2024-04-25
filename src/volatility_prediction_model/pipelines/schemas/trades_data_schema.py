"""Data schema for trades data"""
from pandera import Column, DataFrameSchema

trades_data_schema = DataFrameSchema(
    {
        "Price": Column("float32", required=True),
        "Quantity": Column("float32", required=True),
        "Type": Column(str, required=True),
    }
)
