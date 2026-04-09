document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('new-process-form');

    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        const token = localStorage.getItem('token');
        if (!token) {
            alert("Sessão expirada. Faça login novamente.");
            window.location.href = 'index.html';
            return;
        }

        const formData = new FormData(form);
        const data = Object.fromEntries(formData.entries());

        try {
            // 1. Criar o Cliente
            const clientRes = await fetch(`${API}/clients/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({
                    name: data.client_name,
                    document: data.client_document,
                    email: data.client_email
                })
            });

            if (!clientRes.ok) {
                const err = await clientRes.json();
                throw new Error(err.detail || "Erro ao cadastrar cliente.");
            }

            const client = await clientRes.json();
            const clientId = client.id;

            // 2. Criar o Processo
            const processRes = await fetch(`${API}/processes/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({
                    number: data.process_number,
                    court: data.process_court,
                    type: data.process_type,
                    client_id: clientId,
                    status: 'ativo'
                })
            });

            if (!processRes.ok) {
                const err = await processRes.json();
                throw new Error(err.detail || "Erro ao cadastrar processo.");
            }

            const process = await processRes.json();
            
            alert("Processo e Cliente cadastrados com sucesso!");
            
            // 3. Redirecionar para a página do processo (assumindo que existe uma dashboard do caso)
            // Se houver uma página de detalhes, redireciona para lá. 
            // Como padrão, vamos para a lista de processos ou dashboard
            window.location.href = `process.html?id=${process.id}`;

        } catch (error) {
            alert(error.message);
            console.error(error);
        }
    });
});
