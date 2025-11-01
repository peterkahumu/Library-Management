
document.addEventListener("DOMContentLoaded", (e) => {

    // hide help text in input fields.
    const helpText = document.querySelectorAll(".form-text")
    helpText.forEach(e => e.style.display = "none")

    // for date of birth field, remove default value.
    const date_of_birth = document.querySelector("#id_date_of_birth")
    if (date_of_birth) {
        date_of_birth.value = ""
    }
})
