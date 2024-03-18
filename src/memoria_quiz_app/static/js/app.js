const button = document.getElementById('spinner-button');
const form = document.getElementById('signupForm');

button.onclick = () => {
    const spinner = document.getElementById('spinner');
    spinner.removeAttribute('hidden');
    button.setAttribute('disabled', 'disabled');
    button_text = document.getElementById('button-text');
    button_text.innerHTML = 'Génération en cours...';
    form.submit();
}
