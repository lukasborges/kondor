{
    const hasAutocompleteUsername = (el) =>
        (el.getAttribute("autocomplete") || "").toLowerCase().split(/\s+/).includes("username");

    const isEmailInput = (el) => (el.getAttribute("type") || "").toLowerCase() === "email";

    const looksLikeUsername = (el) => /user|email|login|identifier/i.test(el.name + " " + el.id);

    window.__kondorPickUsernameField = (fields) =>
        fields.find(hasAutocompleteUsername)
            || fields.find(isEmailInput)
            || fields.find(looksLikeUsername)
            || null;
}
