from setuptools import setup, find_packages

setup(
    name='PL_winners_predictor',
    version='0.1',
    packages=find_packages(),
    install_requires=[
        'pandas==2.0.0',
        'numpy==1.25.0',
        'plotly==5.10.0',
        'streamlit==1.14.0',
        'scipy==1.10.0',
    ],

)
