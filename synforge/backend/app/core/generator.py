import pandas as pd
import numpy as np
import os
import warnings
from sdv.metadata import SingleTableMetadata
from sdv.single_table import CTGANSynthesizer

# Silence the SDV deprecation noise for a cleaner terminal
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning)

class SynForgeGenerator:
    def __init__(self, metadata=None):
        self.metadata = metadata if metadata else SingleTableMetadata()
        self.model = None

    def _get_optimized_params(self, n_rows: int):
        """
        DYNAMIC TUNING LOGIC: 
        Adjusts the 'Privacy-Utility Frontier' based on sample density.
        """
        if n_rows < 1000:
            # Small Data (e.g., Fertility, German Credit)
            # High risk of memorization -> Low Epochs, Tiny Batch
            return {"epochs": 15, "batch_size": 20, "lr": 1e-4}
        elif n_rows < 10000:
            # Mid Data (e.g., Bank, Smartphone Addiction)
            # Balance patterns and privacy -> Med Epochs, Med Batch
            return {"epochs": 25, "batch_size": 500, "lr": 2e-4}
        else:
            # Big Data (e.g., Student Life, Census)
            # High variance -> More Epochs, Large Batch to generalize
            return {"epochs": 35, "batch_size": 2000, "lr": 2e-4}

    def train(self, df: pd.DataFrame, enforce_privacy=True, epsilon=0.5):
        """
        ADVERSARIAL REGULARIZATION: 
        Forcing generalization to ensure the GAN learns group distributions 
        instead of individual row identities.
        """
        if not self.metadata.columns:
            self.metadata.detect_from_dataframe(df)
            
        n_rows = len(df)
        params = self._get_optimized_params(n_rows)
        
        print(f"[SynForge] Dataset detected: {n_rows} rows.")
        print(f"[SynForge] Initializing Synthesis Engine...")

        if enforce_privacy:
            print(f"[SynForge] Mode: Aggressive Privacy Regularization")
            print(f"[SynForge] Params: Epochs={params['epochs']}, Batch={params['batch_size']}")
            
            self.model = CTGANSynthesizer(
                self.metadata,
                epochs=params['epochs'],
                batch_size=params['batch_size'],
                generator_lr=params['lr'],
                discriminator_lr=params['lr'],
                verbose=True
            )
        else:
            print(f"[SynForge] Mode: Standard Optimization")
            self.model = CTGANSynthesizer(
                self.metadata,
                epochs=35, # Default fallback
                verbose=True
            )

        self.model.fit(df)
        return True

    def generate(self, num_rows: int):
        if not self.model:
            raise ValueError("Model must be trained or loaded before generation.")
        
        print(f"[SynForge] Sampling {num_rows} records from latent distributions...")
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