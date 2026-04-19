// ═══ Loading Spinner ═══
const spinner = document.getElementById('global-spinner');

// Show spinner on form submit
document.querySelectorAll('form.needs-spinner').forEach(form => {
  form.addEventListener('submit', function(e) {
    if (this.checkValidity()) {
      if (spinner) spinner.classList.remove('hidden');
    }
  });
});

// ═══ Flash message auto-dismiss ═══
setTimeout(() => {
  document.querySelectorAll('.flash-msg').forEach(el => {
    el.style.transition = 'opacity .4s';
    el.style.opacity = '0';
    setTimeout(() => el.remove(), 400);
  });
}, 4500);

// ═══ Client-side validation for prediction form ═══
document.addEventListener('DOMContentLoaded', function() {
  const predictForm = document.getElementById('wizardForm');
  if (!predictForm) return;

  predictForm.addEventListener('submit', function(e) {
    const incomeField = document.querySelector('[name="ApplicantIncome"]');
    const coIncomeField = document.querySelector('[name="CoapplicantIncome"]');
    const loanField = document.querySelector('[name="LoanAmount"]');
    const termField = document.querySelector('[name="Loan_Amount_Term"]');

    let valid = true;
    const showError = (el, msg) => {
      el.style.borderColor = '#ef4444';
      let err = el.parentElement.querySelector('.val-err');
      if (!err) {
        err = document.createElement('p');
        err.className = 'val-err text-red-400 text-xs mt-1';
        el.parentElement.appendChild(err);
      }
      err.textContent = msg;
      valid = false;
    };
    const clearError = (el) => {
      el.style.borderColor = '';
      const err = el.parentElement.querySelector('.val-err');
      if (err) err.remove();
    };

    if (incomeField) {
      clearError(incomeField);
      if (parseFloat(incomeField.value) < 0) {
        showError(incomeField, 'Income cannot be negative.');
      }
    }
    if (coIncomeField) {
      clearError(coIncomeField);
      if (parseFloat(coIncomeField.value) < 0) {
        showError(coIncomeField, 'Co-applicant income cannot be negative.');
      }
    }
    if (loanField) {
      clearError(loanField);
      if (parseFloat(loanField.value) <= 0) {
        showError(loanField, 'Loan amount must be greater than 0.');
      }
    }
    if (termField) {
      clearError(termField);
      if (parseFloat(termField.value) <= 0) {
        showError(termField, 'Loan term must be greater than 0 months.');
      }
    }

    if (!valid) {
      e.preventDefault();
      return;
    }
    // Show spinner
    if (spinner) spinner.classList.remove('hidden');
  });
});

// ═══ Credit Score Animated Bar ═══
function animateScoreBar(score) {
  const bar = document.getElementById('score-bar-fill');
  const label = document.getElementById('score-label');
  if (!bar) return;
  const pct = Math.round((score / 900) * 100);
  setTimeout(() => { bar.style.width = pct + '%'; }, 100);
  if (label) label.textContent = score + ' / 900';
}

// ═══ SVG Confidence Ring ═══
function animateRing(confidence) {
  const ring = document.getElementById('conf-ring');
  const text = document.getElementById('conf-text');
  if (!ring) return;
  const r = 36;
  const circ = 2 * Math.PI * r;
  const offset = circ - (confidence / 100) * circ;
  ring.style.strokeDasharray = circ;
  ring.style.strokeDashoffset = circ;
  setTimeout(() => { ring.style.strokeDashoffset = offset; }, 100);
  if (text) text.textContent = confidence + '%';
}
