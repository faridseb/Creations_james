// view_referrals.js

$(document).ready(function() {
    // Fonction pour charger les filleuls via AJAX
    function loadReferrals() {
        $.ajax({
            url: '/api/referrals/',  // Endpoint de votre API pour récupérer les filleuls
            type: 'GET',
            success: function(data) {
                // Construction du HTML des filleuls à partir des données reçues
                var html = '';
                data.forEach(function(referral) {
                    html += '<div class="cadre-bleu mb-3">';
                    html += '<div class="card">';
                    html += '<div class="card-body text-center">';
                    html += '<img src="' + avatarUrl(referral.email, 30) + '" class="avatar" alt="Avatar de ' + referral.get_full_name + '">';
                    html += '<p>' + referral.email + '</p>';
                    html += '</div></div></div>';
                });
                // Insérer le HTML construit dans le conteneur des filleuls
                $('#referral-container .row').html(html);
            },
            error: function(error) {
                console.error('Erreur lors du chargement des filleuls :', error);
            }
        });
    }

    // Appeler la fonction pour charger les filleuls au chargement de la page
    loadReferrals();
});
