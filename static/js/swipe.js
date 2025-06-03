/**
 * Funzionalità di swipe per le card dei film
 * Gestisce le interazioni touch e mouse per lo swipe in stile Tinder
 */

class SwipeHandler {
    constructor() {
        // Elemento contenitore di tutte le card
        this.cardStack = document.getElementById('cardStack');
        this.currentCard = null;      // Card attualmente trascinata
        this.isDragging = false;      // Flag per indicare se l'utente sta trascinando
        this.startX = 0;              // Coordinata X di inizio trascinamento
        this.startY = 0;              // Coordinata Y di inizio trascinamento
        this.currentX = 0;            // Coordinata X corrente durante il drag
        this.currentY = 0;            // Coordinata Y corrente durante il drag
        this.threshold = 100;         // Distanza minima (px) per considerare valido lo swipe
        this.rotationFactor = 0.1;    // Fattore di rotazione in base alla distanza di swipe

        this.init();
    }

    init() {
        // Se non esiste un contenitore per le card, interrompe l'inizializzazione
        if (!this.cardStack) return;

        this.bindEvents();      // Collega i listener per mouse e touch
        this.updateCardStack(); // Aggiorna le proprietà visive di ciascuna card nella pila
    }

    bindEvents() {
        // Eventi mouse
        this.cardStack.addEventListener('mousedown', this.handleStart.bind(this));
        document.addEventListener('mousemove', this.handleMove.bind(this));
        document.addEventListener('mouseup', this.handleEnd.bind(this));

        // Eventi touch (aggiunge { passive: false } per evitare scroll indesiderati)
        this.cardStack.addEventListener('touchstart', this.handleStart.bind(this), { passive: false });
        document.addEventListener('touchmove', this.handleMove.bind(this), { passive: false });
        document.addEventListener('touchend', this.handleEnd.bind(this));
        // Gestione interruzione touch
        document.addEventListener('touchcancel', this.handleEnd.bind(this));

        // Disabilita il menu contestuale su long press
        this.cardStack.addEventListener('contextmenu', (e) => e.preventDefault());
    }

    handleStart(e) {
        // Recupera la card cliccata/toccata più in alto nella pila
        const card = e.target.closest('.movie-card');
        if (!card || card !== this.getTopCard()) return;

        // Verifica se l'utente è autenticato; se no, blocca lo swipe
        if (!this.isUserAuthenticated()) {
            return;
        }

        this.currentCard = card;
        this.isDragging = true;

        // Se è un mousedown, è un MouseEvent; altrimenti è TouchEvent
        const point = e.type === 'mousedown' ? e : e.touches[0];
        this.startX = point.clientX;
        this.startY = point.clientY;
        this.currentX = point.clientX;
        this.currentY = point.clientY;

        // Aggiunge classe per evidenziare che la card è in fase di trascinamento
        this.currentCard.classList.add('dragging');

        // Prevent default per evitare lo scrolling su dispositivi touch
        if (e.type === 'touchstart') {
            e.preventDefault();
        }
    }

    handleMove(e) {
        // Se non è in corso un trascinamento o non c'è una card corrente, esce
        if (!this.isDragging || !this.currentCard) return;

        // Aggiorna le coordinate correnti in base al tipo di evento
        const point = e.type === 'mousemove' ? e : e.touches[0];
        this.currentX = point.clientX;
        this.currentY = point.clientY;

        // Calcola la distanza trascinata lungo X e Y
        const deltaX = this.currentX - this.startX;
        const deltaY = this.currentY - this.startY;
        const rotation = deltaX * this.rotationFactor; // Rotazione proporzionale a deltaX

        // Applica la trasformazione (traslazione + rotazione) alla card
        this.currentCard.style.transform = `translateX(${deltaX}px) translateY(${deltaY}px) rotate(${rotation}deg)`;

        // Mostra o nasconde gli indicatori di "like"/"dislike" in base alla direzione
        this.updateSwipeIndicators(deltaX);

        // Evita lo scrolling della pagina durante il trascinamento touch
        if (e.type === 'touchmove') {
            e.preventDefault();
        }
    }

    handleEnd(e) {
        // Se non stava trascinando o non c'è card corrente, esce
        if (!this.isDragging || !this.currentCard) return;

        // Rimuove subito la classe "dragging"
        this.currentCard.classList.remove('dragging');

        // Distanza finale trascinata lungo X
        const deltaX = this.currentX - this.startX;
        const absDeltaX = Math.abs(deltaX);

        // Se la distanza supera la soglia, considera lo swipe valido
        if (absDeltaX > this.threshold) {
            const liked = deltaX > 0; // Se deltaX positivo => like, altrimenti dislike
            this.swipeCard(liked);
        } else {
            // Altrimenti, riporta la card al centro
            this.resetCard();
        }

        this.isDragging = false;
        this.currentCard = null;
    }

    updateSwipeIndicators(deltaX) {
        // Mostra l'indicatore di "like" o "dislike" in base al deltaX
        if (!this.currentCard) return;

        if (deltaX > 50) {
            // Se trascinata sufficientemente a destra
            this.currentCard.classList.add('swiping-right');
            this.currentCard.classList.remove('swiping-left');
        } else if (deltaX < -50) {
            // Se trascinata sufficientemente a sinistra
            this.currentCard.classList.add('swiping-left');
            this.currentCard.classList.remove('swiping-right');
        } else {
            // Se non supera nessuna soglia, rimuove eventuali indicatori
            this.currentCard.classList.remove('swiping-right', 'swiping-left');
        }
    }

    swipeCard(liked) {
        // Se non c'è una card corrente, esce
        if (!this.currentCard) return;

        // Ottiene l'ID del film dalla card
        const movieId = this.currentCard.getAttribute('data-movie-id');

        // Aggiunge classi per l'animazione di rimozione e per indicare "liked" o "disliked"
        this.currentCard.classList.add('removing', liked ? 'liked' : 'disliked');

        // Invia la valutazione al server
        this.rateMovie(movieId, liked);

        // Dopo 300ms (tempo animazione), rimuove la card dal DOM
        setTimeout(() => {
            // Recupera nuovamente la card in caso sia cambiata
            const removingCard = document.querySelector(`.movie-card.removing[data-movie-id="${movieId}"]`);
            if (removingCard && removingCard.parentNode) {
                removingCard.remove();
                this.updateCardStack();    // Aggiorna le proprietà visive delle restanti card
                this.checkForEmptyState(); // Verifica se la pila è vuota
            }
        }, 300);
    }

    resetCard() {
        // Riporta la card al suo stato iniziale
        if (!this.currentCard) return;

        // Ripristina trasformazioni e rimuove eventuali classi che modificano opacità/trasparenza
        this.currentCard.style.transform = '';
        this.currentCard.classList.remove(
            'swiping-right',
            'swiping-left',
            'dragging',
            'liked',
            'disliked',
            'removing'
        );
    }

    getTopCard() {
        // Restituisce la prima card non contrassegnata come in rimozione
        const cards = this.cardStack.querySelectorAll('.movie-card:not(.removing)');
        return cards.length > 0 ? cards[0] : null;
    }

    isUserAuthenticated() {
        // Verifica la presenza di un elemento di navigazione utente (#navbarDropdown)
        // Se esiste, l'utente è loggato; altrimenti è anonimo
        return document.querySelector('#navbarDropdown') !== null;
    }

    updateCardStack() {
        // Aggiorna l'ordine visivo (z-index, scala, opacità) delle card rimanenti
        const cards = this.cardStack.querySelectorAll('.movie-card:not(.removing)');
        cards.forEach((card, index) => {
            if (index === 0) {
                // Card in cima alla pila: più grande e completamente visibile
                card.style.zIndex = 5;
                card.style.transform = 'scale(1)';
                card.style.opacity = '1';
            } else if (index === 1) {
                // Seconda card: leggermente più piccola e sfumata
                card.style.zIndex = 4;
                card.style.transform = 'scale(0.98) translateY(10px)';
                card.style.opacity = '0.9';
            } else if (index === 2) {
                // Terza card: ancora più piccola
                card.style.zIndex = 3;
                card.style.transform = 'scale(0.96) translateY(20px)';
                card.style.opacity = '0.8';
            } else {
                // Tutte le altre card: misurazioni di base
                card.style.zIndex = 2;
                card.style.transform = 'scale(0.94) translateY(30px)';
                card.style.opacity = '0.7';
            }
        });
    }

    checkForEmptyState() {
        // Se non ci sono più card visibili, mostra lo stato "vuoto"
        const remainingCards = this.cardStack.querySelectorAll('.movie-card:not(.removing)');
        if (remainingCards.length === 0) {
            document.getElementById('emptyState').style.display = 'block';
        }
    }

    rateMovie(movieId, liked) {
        // Mostra un overlay di caricamento (se presente)
        const loadingOverlay = document.getElementById('loadingOverlay');
        if (loadingOverlay) {
            loadingOverlay.style.display = 'flex';
        }

        // Prepara FormData per la richiesta POST
        const formData = new FormData();
        formData.append('movie_id', movieId);
        formData.append('liked', liked);

        // Invio della richiesta al server
        fetch('/rate_movie', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            // Nasconde l'overlay di caricamento
            if (loadingOverlay) {
                loadingOverlay.style.display = 'none';
            }

            if (data.success) {
                // Se successo, aggiorna il conteggio dei "mi piace" nella UI
                const likedCountElements = document.querySelectorAll('#liked-count, #hero-liked-count');
                likedCountElements.forEach(el => {
                    el.textContent = data.liked_count;
                });

                // Mostra un breve messaggio di conferma
                this.showToast(`Film ${data.action}!`);
            } else {
                console.error('Errore nel votare il film:', data.error);
                this.showToast('Errore nel votare il film', 'error');
            }
        })
        .catch(error => {
            // In caso di errore di rete, nasconde l'overlay e mostra un toast di errore
            if (loadingOverlay) {
                loadingOverlay.style.display = 'none';
            }
            console.error('Errore di rete:', error);
            this.showToast('Si è verificato un errore di rete', 'error');
        });
    }

    showToast(message, type = 'success') {
        // Mostra un breve toast di feedback all'utente
        const toast = document.getElementById('successToast');
        const toastMessage = document.getElementById('toastMessage');
        if (!toast || !toastMessage) return;

        // Imposta il testo del toast
        toastMessage.textContent = message;

        // Usa l'API di Bootstrap per mostrare il toast
        const bsToast = new bootstrap.Toast(toast);
        bsToast.show();
    }
}

// Inizializza la funzionalità di swipe creando un'istanza di SwipeHandler
function initializeSwipe() {
    new SwipeHandler();
}

// Funzione pubblica per eseguire lo swipe tramite click su pulsanti (like/pass)
window.rateMovie = function(movieId, liked) {
    // Prima verifica se l'utente è autenticato
    if (!document.querySelector('#navbarDropdown')) {
        // Se non autenticato, reindirizza alla pagina di login
        window.location.href = '/auth/login';
        return;
    }

    const cardStack = document.getElementById('cardStack');
    const topCard = cardStack.querySelector('.movie-card:not(.removing)');

    // Se la card in cima ha lo stesso movieId, esegue l'animazione e lo swipe
    if (topCard && topCard.getAttribute('data-movie-id') == movieId) {
        animateButtonSwipe(topCard, liked);

        // Dopo una breve attesa, istanzia SwipeHandler per eseguire lo swipe
        setTimeout(() => {
            const swipeHandler = new SwipeHandler();
            swipeHandler.currentCard = topCard;
            swipeHandler.swipeCard(liked);
        }, 200);
    }
};

// Animazione di preview dello swipe quando si clicca sui pulsanti like/pass
function animateButtonSwipe(card, liked) {
    // Direzione e valori di transform per like o dislike
    const translateX = liked ? '80px' : '-80px';
    const rotation = liked ? '8deg' : '-8deg';

    // Mostra subito l'indicatore di swipe
    if (liked) {
        card.classList.add('swiping-right');
        card.classList.remove('swiping-left');
    } else {
        card.classList.add('swiping-left');
        card.classList.remove('swiping-right');
    }

    // Applica la trasformazione iniziale (più marcata) con transizione
    card.style.transition = 'transform 0.2s ease-out';
    card.style.transform = `translateX(${translateX}) rotate(${rotation}) scale(1.02)`;

    // Dopo 100ms, applica una leggera correzione per l'effetto "rimbalzo"
    setTimeout(() => {
        const partialTranslate = liked ? '40px' : '-40px';
        const partialRotation = liked ? '4deg' : '-4deg';
        card.style.transform = `translateX(${partialTranslate}) rotate(${partialRotation}) scale(1.01)`;
    }, 100);

    // Dopo 200ms, ripristina transizione e trasformazione per permettere lo swipe finale
    setTimeout(() => {
        card.style.transition = '';
        card.style.transform = '';
        card.classList.remove('swiping-right', 'swiping-left');
    }, 200);
}
