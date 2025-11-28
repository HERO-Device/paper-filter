import pandas as pd
import sys
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

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

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

def main():
    """Main function for command line usage"""

    if len(sys.argv) < 2:
        print("Usage: python data_processing.py <input.csv> [output.csv]")
        print("\nExample:")
        print("\n python data_processing.py ../data/raw/scopus_export.csv")
        print("\n python data_processing.py ../data/raw/scopus_export.csv ../data/processed/deduplicated.csv")
        sys.exit(1)

    input_file = Path(sys.argv[1])

    if not input_file.exists():
        print(f"Input file not found {input_file}")
        sys.exit(1)

    if len(sys.argv) > 2:
        output_path = Path(sys.argv[2])
    else:
        output_path = input_file.parent / "deduplicated.csv"

    processor = PaperProcessor(input_file)
    processor.load_data()

    print(f"\nColumns in dataset: {len(processor.df.columns)}")
    title_col = processor.get_title_column()
    print(f"Title column: '{title_col}'")

    print(f"\nRemoving duplicates based on '{title_col}'...")
    processor.remove_duplicates()

    print(f"\nSaving to: {output_path}")
    processor.save_processed(output_path)

    stats = processor.get_stats()
    print("Processing Summary")
    print(f"Original papers:     {stats['original_count']:,}")
    print(f"Duplicates removed:  {stats['removed']:,} ({stats['removal_rate']:.1f}%)")
    print(f"Final count:         {stats['current_count']:,}")
    print(f"Output file:         {output_path}")

    print("\nDeduplication complete!")


if __name__ == "__main__":
    main()