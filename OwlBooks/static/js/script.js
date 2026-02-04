async function updateJSON() {
    const updatedData = {};
    document.querySelectorAll('.json-input').forEach(input => {
        try {
            updatedData[input.name] = JSON.parse(input.value);
        } catch (e) {
            updatedData[input.name] = input.value; // Fallback für einfache Werte
        }
    });
    try {
        const response = await fetch('/update', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(updatedData)
        });
        const result = await response.json();
        alert(result.message || result.error);
    } catch (error) {
        alert('Fehler beim Aktualisieren der JSON-Daten.');
    }
}

async function generatePDF() {
    try {
        const response = await fetch('/generate_pdf', {
            method: 'POST'
        });
        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'Rechenregelsteuerung.pdf';
            document.body.appendChild(a);
            a.click();
            a.remove();
        } else {
            alert('Fehler bei der PDF-Erstellung.');
        }
    } catch (error) {
        alert('Fehler beim Erstellen der PDF.');
    }
}

async function generateExcel() {
    try {
        const response = await fetch('/generate_excel', {
            method: 'POST'
        });
        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'Schnittstelle.xlsx';
            document.body.appendChild(a);
            a.click();
            a.remove();
        } else {
            alert('Fehler bei der Excel-Erstellung.');
        }
    } catch (error) {
        alert('Fehler beim Erstellen der Excel-Datei.');
    }
}