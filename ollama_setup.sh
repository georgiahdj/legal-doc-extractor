#!/bin/bash
# ollama_setup.sh
#
# Κατεβάζει το LLaVA model μετά την εκκίνηση του Ollama.
# Τρέχει μία φορά — μετά είναι αποθηκευμένο στο volume.

echo "Waiting for Ollama to start..."

# Περιμένω μέχρι το Ollama να είναι έτοιμο
until curl -s http://ollama:11434/api/tags > /dev/null 2>&1; do
    echo "Ollama not ready yet, waiting..."
    sleep 2
done

echo "Ollama is ready!"

# ελεγχος αν το LLaVA είναι ήδη κατεβασμένο
if curl -s http://ollama:11434/api/tags | grep -q "llava"; then
    echo "LLaVA already downloaded!"
else
    echo "Downloading LLaVA model (this may take a while)..."
    curl -X POST http://ollama:11434/api/pull \
         -H "Content-Type: application/json" \
         -d '{"name": "llava"}'
    echo "LLaVA downloaded!"
fi