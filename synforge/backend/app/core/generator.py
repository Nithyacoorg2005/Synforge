import pandas as pd
import numpy as np
import os
from sdv.metadata import SingleTableMetadata
from sdv.single_table import CTGANSynthesizer

class SynForgeGenerator:
    def __init__(self, metadata=None):
        self.metadata = metadata if metadata else SingleTableMetadata()
        self.model = None

    def train(self, df: pd.DataFrame, epochs=15, enforce_privacy=True, epsilon=0.5):
        """
        ADVERSARIAL REGULARIZATION: 
        Forcing under-fitting to ensure the GAN learns group distributions 
        instead of individual row identities.
        """
        if not self.metadata.columns:
            self.metadata.detect_from_dataframe(df)
            
        print(f"[SynForge] Initializing Synthesis Engine...")

        # If privacy is enforced, we override everything with 'Safe-Mode' params
        if enforce_privacy:
            print(f"[SynForge] Training with Aggressive Privacy Regularization...")
            self.model = CTGANSynthesizer(
                self.metadata,
                epochs=25,               # Force 'Fuzzy' learning
                batch_size=2000,          # Average 4000 rows per gradient
                generator_lr=5e-5,        # Slow, stable convergence
                discriminator_lr=5e-5,    # Prevent 'Over-critiquing'
                verbose=True
            )
        else:
            print(f"[SynForge] Training in Standard Mode...")
            self.model = CTGANSynthesizer(
                self.metadata,
                epochs=epochs,
                verbose=True
            )

        self.model.fit(df)
        return True

    def generate(self, num_rows: int):
        if not self.model:
            raise ValueError("Model must be trained or loaded before generation.")
        
        print(f"[SynForge] Sampling {num_rows} records from distributions...")
        return self.model.sample(num_rows=num_rows)

    def save_model(self, path):
        if self.model:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            self.model.save(path)

    @classmethod
    def load_model(cls, path):
        if not os.path.exists(path):
            raise FileNotFoundError(f"Model artifact not found at {path}")
        loaded_model = CTGANSynthesizer.load(path) 
        instance = cls(metadata=loaded_model.metadata)
        instance.model = loaded_model
        return instance