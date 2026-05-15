// Fonction pour ajuster la taille des images dans un carousel
function adjustImageSize(carousel) {
    const carouselWidth = carousel.offsetWidth;
    const images = carousel.querySelectorAll('.carousel-item img');

    images.forEach(function(image) {
        image.style.width = carouselWidth + 'px';
        image.style.height = 'auto';
    });
}

// Fonction pour aligner les images deux par deux sur les écrans de taille moyenne et petite
function alignImages(carousel) {
    const screenWidth = window.innerWidth;
    const images = carousel.querySelectorAll('.carousel-item img');

    if (screenWidth <= 992) {
        images.forEach(function(image, index) {
            if (index % 2 === 0) {
                image.style.marginRight = '10px';
            } else {
                image.style.marginRight = '0';
            }
        });
    } else {
        images.forEach(function(image) {
            image.style.marginRight = '0';
        });
    }
}

document.addEventListener('DOMContentLoaded', function() {
    const carousels = document.querySelectorAll('.carousel');

    carousels.forEach(function(carousel) {
        adjustImageSize(carousel);
        alignImages(carousel);

        window.addEventListener('resize', function() {
            adjustImageSize(carousel);
            alignImages(carousel);
        });
    });
});
