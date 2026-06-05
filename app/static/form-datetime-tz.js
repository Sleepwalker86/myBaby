/**
 * datetime-local liefert keine Zeitzone; vor dem Absenden in UTC-ISO wandeln,
 * damit der Server den korrekten Moment speichern kann (z. B. im Ausland).
 * Formulare mit Klasse "client-tz-submit" werden behandelt.
 *
 * Optional: data-inject-client-now="end_time" — verstecktes Feld mit aktuellem
 * Zeitpunkt (UTC-ISO), z. B. für Schlaf beenden ohne datetime-local.
 */
(function () {
    function localDatetimeLocalValueToIso(value) {
        if (!value || typeof value !== 'string') {
            return '';
        }
        var m = value.match(/^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})(?::(\d{2}))?/);
        if (!m) {
            return '';
        }
        var y = parseInt(m[1], 10);
        var mo = parseInt(m[2], 10) - 1;
        var d = parseInt(m[3], 10);
        var h = parseInt(m[4], 10);
        var mi = parseInt(m[5], 10);
        var dt = new Date(y, mo, d, h, mi, 0, 0);
        if (isNaN(dt.getTime())) {
            return '';
        }
        return dt.toISOString();
    }

    function injectClientNow(form) {
        var name = form.getAttribute('data-inject-client-now');
        if (!name) {
            return;
        }
        var existing = form.querySelector('input[type="hidden"][name="' + name + '"]');
        var iso = new Date().toISOString();
        if (existing) {
            existing.value = iso;
        } else {
            var h = document.createElement('input');
            h.type = 'hidden';
            h.name = name;
            h.value = iso;
            form.appendChild(h);
        }
    }

    function convertDatetimeLocalInputs(form) {
        form.querySelectorAll('input[type="datetime-local"]').forEach(function (inp) {
            if (!inp.name) {
                return;
            }
            var v = inp.value;
            if (!v) {
                return;
            }
            var iso = localDatetimeLocalValueToIso(v);
            if (!iso) {
                return;
            }
            var key = inp.id || inp.name;
            var hid = form.querySelector('input[type="hidden"][data-tz-convert-for="' + key + '"]');
            if (!hid) {
                hid = document.createElement('input');
                hid.type = 'hidden';
                hid.setAttribute('data-tz-convert-for', key);
                form.appendChild(hid);
            }
            hid.name = inp.name;
            hid.value = iso;
            inp.removeAttribute('name');
        });
    }

    document.querySelectorAll('form.client-tz-submit').forEach(function (form) {
        form.addEventListener('submit', function () {
            injectClientNow(form);
            convertDatetimeLocalInputs(form);
        });
    });
})();
