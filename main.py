from app import app

if __name__ == '__main__':
    # Avvio del server Flask
    # - host '0.0.0.0' significa "ascolta su tutte le interfacce di rete"
    # - porta 5000 è la porta di default per lo sviluppo
    # - debug=True abilita il riavvio automatico e mostra eventuali errori in dettaglio
    app.run(host='0.0.0.0', port=5000, debug=True)