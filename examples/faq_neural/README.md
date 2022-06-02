This example illustrates how a `dialogic` bot could work in
two modes: FAQ (default) and chitchat (fallback mode).
Both modes are implemented based on neural networks: 
a BERT-based encoder for FAQ matching, 
and a T5-based model for chitchat response generation.

The interface is usual: to play with a commandline demo, run
```commandline
pip install -r requrements.txt
python main.py --cli
```
