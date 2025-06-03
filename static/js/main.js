/**
  * Gestisce le interazioni generali dell'interfaccia utente e funzioni utili
 */

document.addEventListener('DOMContentLoaded', function() {
    // Quando il DOM è completamente caricato, inizializza l'app
    initializeApp();
});

function initializeApp() {
    // Inizializza i tooltip se Bootstrap è disponibile
    if (typeof bootstrap !== 'undefined') {
        // Seleziona tutti gli elementi con l'attributo data-bs-toggle="tooltip" e attiva i tooltip di Bootstrap
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function(tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }

    // Aggiunge lo scorrimento fluido (smooth scrolling) per i link di ancoraggio
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();  // Previene il comportamento di default del link
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                // Scorre la pagina fino alla sezione di destinazione con animazione fluida
                target.scrollIntoView({
                    behavior: 'smooth'
                });
            }
        });
    });

    // Attiva l'animazione delle card al caricamento della pagina
    animateCardsOnLoad();

    // Inizializza le scorciatoie da tastiera
    initializeKeyboardShortcuts();
}

function animateCardsOnLoad() {
    // Seleziona tutte le card dei film
    const cards = document.querySelectorAll('.movie-card');
    cards.forEach((card, index) => {
        // Applica uno stato iniziale per rendere invisibili e spostate verso il basso
        card.style.opacity = '0';
        card.style.transform = 'translateY(50px) scale(0.9)';

        // Con un timeout progressivo per ogni card, ripristina le proprietà per creare l'animazione
        setTimeout(() => {
            card.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
            card.style.opacity = '';
            card.style.transform = '';
        }, index * 100);
    });
}

function initializeKeyboardShortcuts() {
    // Aggiunge un listener per gli eventi di pressione dei tasti
    document.addEventListener('keydown', function(e) {
        // Ignora le scorciatoie se l'utente sta digitando in un campo input o textarea
        if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') {
            return;
        }

        // Seleziona la prima card non contrassegnata come in rimozione
        const topCard = document.querySelector('.movie-card:not(.removing)');
        if (!topCard) return;

        // Recupera l'attributo data-movie-id della card in evidenza
        const movieId = topCard.getAttribute('data-movie-id');

        // Gestisce diverse combinazioni di tasti per passare o mettere like rapidamente
        switch(e.key) {
            case 'ArrowLeft':
            case 'x':
            case 'X':
                e.preventDefault();
                // Se preme freccia sinistra o X, segna il film come "non mi piace"
                rateMovie(movieId, false);
                break;
            case 'ArrowRight':
            case 'l':
            case 'L':
                e.preventDefault();
                // Se preme freccia destra o L, segna il film come "mi piace"
                rateMovie(movieId, true);
                break;
            case 'i':
            case 'I':
                e.preventDefault();
                // Se preme I, mostra i dettagli del film
                showMovieDetails(movieId);
                break;
            case 'r':
            case 'R':
                // Se preme Ctrl+R (o Cmd+R su Mac) innesca il reset delle preferenze
                if (e.ctrlKey || e.metaKey) {
                    e.preventDefault();
                    resetPreferences();
                }
                break;
        }
    });
}

function showMovieDetails(movieId) {
    // Cerca la card corrispondente al movieId
    const card = document.querySelector(`[data-movie-id="${movieId}"]`);
    if (!card) return;

    // Estrae i dettagli dal DOM della card: titolo, descrizione, genere, anno, regista, valutazione e durata
    const title = card.querySelector('.movie-title').textContent;
    const description = card.querySelector('.movie-description').textContent;
    const genre = card.querySelector('.genre').textContent;
    const year = card.querySelector('.year').textContent;
    // Il testo "Directed by ..." viene rimosso per mostrare solo il nome del regista
    const director = card.querySelector('.movie-director').textContent.replace('Directed by ', '');
    const rating = card.querySelector('.movie-rating span').textContent;
    const duration = card.querySelector('.duration').textContent;

    // Costruisce l'HTML del modal con i dettagli del film
    const modalHtml = `
        <div class="modal fade" id="movieModal" tabindex="-1" aria-labelledby="movieModalLabel" aria-hidden="true">
            <div class="modal-dialog modal-lg">
                <div class="modal-content bg-dark text-light">
                    <div class="modal-header border-secondary">
                        <h5 class="modal-title" id="movieModalLabel">${title}</h5>
                        <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal" aria-label="Close"></button>
                    </div>
                    <div class="modal-body">
                        <div class="row">
                            <div class="col-md-4">
                                <!-- Immagine del poster del film -->
                                <img src="${card.querySelector('.movie-poster img').src}" alt="${title}" class="img-fluid rounded">
                            </div>
                            <div class="col-md-8">
                                <div class="movie-details">
                                    <div class="mb-3">
                                        <!-- Badge con genere, anno, durata e valutazione -->
                                        <span class="badge bg-danger me-2">${genre}</span>
                                        <span class="badge bg-secondary me-2">${year}</span>
                                        <span class="badge bg-secondary me-2">${duration}</span>
                                        <span class="badge bg-warning text-dark">⭐ ${rating}</span>
                                    </div>
                                    <h6>Director</h6>
                                    <p class="text-muted">${director}</p>
                                    <h6>Synopsis</h6>
                                    <p>${description}</p>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="modal-footer border-secondary">
                        <!-- Bottone "Pass" che chiude il modal e invia richiesta di dislike -->
                        <button type="button" class="btn btn-outline-danger" onclick="rateMovie(${movieId}, false); bootstrap.Modal.getInstance(document.getElementById('movieModal')).hide();">
                            <i class="fas fa-times me-1"></i>Pass
                        </button>
                        <!-- Bottone "Like" che chiude il modal e invia richiesta di like -->
                        <button type="button" class="btn btn-danger" onclick="rateMovie(${movieId}, true); bootstrap.Modal.getInstance(document.getElementById('movieModal')).hide();">
                            <i class="fas fa-heart me-1"></i>Like
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `;

    // Rimuove un eventuale modal esistente per evitare duplicati
    const existingModal = document.getElementById('movieModal');
    if (existingModal) {
        existingModal.remove();
    }

    // Inserisce il markup del modal nel body della pagina
    document.body.insertAdjacentHTML('beforeend', modalHtml);

    // Mostra il modal usando le API di Bootstrap
    const modal = new bootstrap.Modal(document.getElementById('movieModal'));
    modal.show();

    // Dopo che il modal viene nascosto, lo rimuove dal DOM per pulizia
    document.getElementById('movieModal').addEventListener('hidden.bs.modal', function() {
        this.remove();
    });
}

function resetPreferences() {
    // Conferma con l'utente prima di resettare tutte le preferenze
    if (!confirm('Sei sicuro di voler resettare tutte le preferenze? Questo cancellerà tutti i tuoi like e dislike.')) {
        return;
    }

    // Mostra un overlay di caricamento (se presente nel DOM)
    const loadingOverlay = document.getElementById('loadingOverlay');
    loadingOverlay.style.display = 'flex';

    // Invia una richiesta POST al server per resettare le preferenze
    fetch('/reset_preferences', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        }
    })
    .then(response => response.json())
    .then(data => {
        // Nasconde l'overlay di caricamento
        loadingOverlay.style.display = 'none';

        if (data.success) {
            // Se la risposta indica successo, ricarica la pagina per aggiornare la lista dei film
            window.location.reload();
        } else {
            // In caso di errore, mostra un toast di tipo 'error'
            showToast('Errore durante il reset delle preferenze', 'error');
        }
    })
    .catch(error => {
        // Nasconde l'overlay e mostra un messaggio di errore in caso di problemi di rete
        loadingOverlay.style.display = 'none';
        console.error('Error:', error);
        showToast('Si è verificato un errore di rete', 'error');
    });
}

function showToast(message, type = 'success') {
    // Seleziona il container del toast e l’elemento dove mostrare il messaggio
    const toast = document.getElementById('successToast');
    const toastMessage = document.getElementById('toastMessage');

    if (toast && toastMessage) {
        // Imposta il testo del messaggio
        toastMessage.textContent = message;

        // Cambia l'icona nel toast in base al tipo (successo o errore)
        const toastElement = toast.querySelector('.toast-header i');
        if (type === 'error') {
            toastElement.className = 'fas fa-exclamation-circle text-danger me-2';
        } else {
            toastElement.className = 'fas fa-check-circle text-success me-2';
        }

        // Mostra il toast con le API di Bootstrap
        const bsToast = new bootstrap.Toast(toast);
        bsToast.show();
    }
}

// Funzione di utilità per formattare la durata in minuti in ore e minuti
function formatDuration(minutes) {
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    return hours > 0 ? `${hours}h ${mins}m` : `${mins}m`;
}

// Funzione di utilità per troncare un testo oltre una lunghezza massima
function truncateText(text, maxLength = 150) {
    if (text.length <= maxLength) return text;
    // Taglia il testo a maxLength caratteri e aggiunge "..."
    return text.substr(0, maxLength).trim() + '...';
}

// Aggiunge uno stato di caricamento a un bottone durante le operazioni asincrone
function addLoadingState(button, text = 'Loading...') {
    button.disabled = true;  // Disabilita il bottone
    const originalText = button.innerHTML;  // Memorizza il testo originale
    // Sostituisce il contenuto con un'icona di caricamento e il testo "Loading..."
    button.innerHTML = `<i class="fas fa-spinner fa-spin me-1"></i>${text}`;

    // Ritorna una funzione di callback per ripristinare lo stato originale del bottone
    return function removeLoadingState() {
        button.disabled = false;
        button.innerHTML = originalText;
    };
}

// Gestisce la comparsa di notifiche quando cambia lo stato di connessione di rete
window.addEventListener('online', function() {
    // Quando la connessione viene ripristinata, mostra un toast di successo
    showToast('Connessione ripristinata', 'success');
});

window.addEventListener('offline', function() {
    // Quando la connessione viene persa, avvisa l'utente con un toast di errore
    showToast('Connessione persa. Alcune funzionalità potrebbero non funzionare.', 'error');
});

// Funzione per scorrere la pagina verso l'alto
function scrollToTop() {
    window.scrollTo({
        top: 0,
        behavior: 'smooth'
    });
}

// Mostra o nasconde il bottone "scroll to top" a seconda della posizione di scroll
window.addEventListener('scroll', function() {
    const scrollButton = document.getElementById('scrollToTop');
    if (window.pageYOffset > 300) {
        if (scrollButton) {
            scrollButton.style.display = 'block';
        }
    } else {
        if (scrollButton) {
            scrollButton.style.display = 'none';
        }
    }
});

// Esporta le funzioni chiave per renderle accessibili globalmente
window.showMovieDetails = showMovieDetails;
window.resetPreferences = resetPreferences;
window.showToast = showToast;
