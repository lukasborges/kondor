{
    const nativeValueDescriptor = (el) =>
        Object.getOwnPropertyDescriptor(Object.getPrototypeOf(el), "value");

    const dispatchValueEvents = (el) => {
        el.dispatchEvent(new Event("input", { bubbles: true }));
        el.dispatchEvent(new Event("change", { bubbles: true }));
    };

    window.__kondorSetFieldValue = (el, value) => {
        const descriptor = nativeValueDescriptor(el);
        if (descriptor && descriptor.set)
            descriptor.set.call(el, value);
        else
            el.value = value;
        dispatchValueEvents(el);
    };
}
