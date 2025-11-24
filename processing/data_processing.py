import pandas as pd
from pathlib import Path

class PaperProcessor:
    """
    Handles loading, de-duplication, and processing of  a.csv file of Scopus papers
    """
    def __init__(self, csv_path):
        self.csv_path = csv_path
        self.df = None
        self.original_count = 0

    def load_data(self):
        """
        Load the .csv file
        """
        print(f"Loading data from {self.csv_path}...")
        self.df = pd.read_csv(self.csv_path)
        self.original_count = len(self.df)
        print(f"Loaded {self.original_count} papers.")
        return self

    def remove_duplicates(self, subset=None, keep="first"):
        """
        Removes duplicate papers,  based on the title/ other columns
        :param subset: Columns to check for duplicates
        :param keep: Which duplicate to keep
        """
        if self.df is None:
            raise ValueError("Data no loaded. Class load_data() first.")

        title_col = self.find_title_column()

        if subset is None:
            subset = [title_col] if title_col else None

        before = len(self.df)
        self.df = self.df.drop_duplicates(subset=subset, keep=keep)
        after = len(self.df)

        print(f"Removed {before - after} duplicate papers.")
        print(f"Remaining papers: {after}")

        return self

    def find_title_column(self):
        """
        Try to automatically find the title column
        """
        possible_names = ["title", "Title", "TITLE", "paper_title", "Paper_Title"]

        for col in self.df.columns:
            if any(name.lower() in col.lower() for name in possible_names):
                return col

        return self.df.columns[0]

    def get_title_column(self):
        """Get the identified name"""
        return self.find_title_column()

    def save_processed(self, output_path):
        """Save the processed dataframe"""
        if self.df is None:
            raise ValueError("No Data to save")

        self.df.to_csv(output_path, index=False)
        print(f"Saved processed data to {output_path}.")
        return self

    def get_stats(self):
        """Get statistics about the dataset"""
        if self.df is None:
            return None

        return {
            "original_count": self.original_count,
            "current_count": len(self.df),
            "columns": list(self.df.columns),
            "removed": self.original_count - len(self.df)
        }

if __name__ == "__main__":
    data_path = Path("../data")
    csv_files = list(data_path.glob("scopus_export*.csv"))

    if not csv_files:
        print("No CSV files found matching 'scopus_export*.csv' in data directory")
    else:
        csv_file = csv_files[0]
        print(f"Processing {csv_file.name}")

        processor = PaperProcessor(csv_file)
        processor.load_data()

        # Show columns
        print(f"\nColumns in dataset: {processor.df.columns.tolist()}")
        print(f"\nTitle column identified as: '{processor.get_title_column()}'")

        # Remove duplicates
        processor.remove_duplicates()

        # Save processed file
        output_path = data_path / "processed_papers.csv"
        processor.save_processed(output_path)

        # Print stats
        print(f"\n=== Processing Summary ===")
        stats = processor.get_stats()
