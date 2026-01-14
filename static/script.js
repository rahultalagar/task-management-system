document.addEventListener("DOMContentLoaded", () => {

    // ---------- FORM VALIDATION ----------
    const forms = document.querySelectorAll("form");

    forms.forEach(form => {
        form.addEventListener("submit", e => {
            let valid = true;
            let passwordError = false;

            const inputs = form.querySelectorAll("input");

            inputs.forEach(input => {
                if (input.value.trim() === "") {
                    input.style.border = "1px solid red";
                    valid = false;
                } else {
                    input.style.border = "1px solid #ccc";
                }

                if (input.type === "password" && input.value.length < 4) {
                    passwordError = true;
                    valid = false;
                }
            });

            if (passwordError) {
                alert("Password must be at least 4 characters");
            }

            if (!valid) {
                e.preventDefault();
            }
        });
    });

    // ---------- AUTO HIDE FLASH MESSAGE ----------
    const flashBox = document.getElementById("flash-wrapper");

    if (flashBox) {
        setTimeout(() => {
            flashBox.style.opacity = "0";
            flashBox.style.transition = "opacity 0.5s ease";

            setTimeout(() => {
                flashBox.remove();
            }, 500);

        }, 3000); // hide after 3 seconds
    }

});
