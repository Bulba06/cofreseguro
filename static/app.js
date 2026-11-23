    async function api(rota, metodo, corpo) {
      const opt = { method: metodo, headers: { "Content-Type": "application/json" } };
      if (corpo) opt.body = JSON.stringify(corpo);
      const r = await fetch(rota, opt);
      const dados = await r.json().catch(() => ({}));
      return { ok: r.ok, dados };
    }
    function msg(id, texto, tipo) {
      const el = document.getElementById(id);
      el.textContent = texto || "";
      el.className = "msg " + (tipo || "");
    }

    async function criarUsuario() {
      const nome = document.getElementById("in-usuario").value;
      const senha = document.getElementById("in-senha-mestra").value;
      const { ok, dados } = await api("/criar_usuario", "POST",
        { nome_usuario: nome, senha_mestra: senha });
      if (ok) msg("msg-bloqueio", "Cofre criado! Agora clique em Desbloquear.", "ok");
      else msg("msg-bloqueio", dados.erro || "Erro ao criar.", "erro");
    }

    async function desbloquear() {
      const nome = document.getElementById("in-usuario").value;
      const senha = document.getElementById("in-senha-mestra").value;
      const { ok, dados } = await api("/desbloquear", "POST",
        { nome_usuario: nome, senha_mestra: senha });
      if (ok) {
        document.getElementById("tela-bloqueio").classList.add("oculto");
        document.getElementById("tela-cofre").classList.remove("oculto");
        listar();
      } else {
        msg("msg-bloqueio", dados.erro || "Erro ao desbloquear.", "erro");
      }
    }

    async function bloquear() {
      await api("/bloquear", "POST");
      document.getElementById("tela-cofre").classList.add("oculto");
      document.getElementById("tela-bloqueio").classList.remove("oculto");
      document.getElementById("in-senha-mestra").value = "";
      msg("msg-bloqueio", "Cofre bloqueado.", "ok");
    }

    function gerarSenha() {
      const cjt = "ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnpqrstuvwxyz23456789!@#$%&*";
      const arr = new Uint32Array(16);
      crypto.getRandomValues(arr);
      let s = "";
      for (const n of arr) s += cjt[n % cjt.length];
      document.getElementById("in-senha").value = s;
    }

    let editandoId = null;

    async function salvar() {
      const corpo = {
        titulo: document.getElementById("in-titulo").value,
        usuario_servico: document.getElementById("in-usuario-servico").value,
        senha: document.getElementById("in-senha").value,
      };
      let resp;
      if (editandoId !== null) {
        corpo.id = editandoId;
        resp = await api("/editar", "POST", corpo);
      } else {
        resp = await api("/adicionar", "POST", corpo);
      }
      const { ok, dados } = resp;
      if (ok) {
        msg("msg-cofre", editandoId !== null ? "Entrada atualizada!" : "Senha adicionada!", "ok");
        cancelarEdicao();
        listar();
      } else {
        msg("msg-cofre", dados.erro || "Erro ao salvar.", "erro");
      }
    }

    function editar(e) {
      editandoId = e.id;
      document.getElementById("in-titulo").value = e.titulo;
      document.getElementById("in-usuario-servico").value = e.usuario_servico || "";
      document.getElementById("in-senha").value = "";
      document.getElementById("btn-salvar").textContent = "Salvar alteração";
      document.getElementById("btn-cancelar").classList.remove("oculto");
      msg("msg-cofre", 'Editando "' + e.titulo + '". Deixe a senha vazia para manter a atual.', "");
      document.getElementById("in-titulo").focus();
    }

    function cancelarEdicao() {
      editandoId = null;
      document.getElementById("in-titulo").value = "";
      document.getElementById("in-usuario-servico").value = "";
      document.getElementById("in-senha").value = "";
      document.getElementById("btn-salvar").textContent = "Adicionar senha";
      document.getElementById("btn-cancelar").classList.add("oculto");
    }

    async function mover(id, direcao) {
      await api("/mover", "POST", { id: id, direcao: direcao });
      listar();
    }

    async function remover(id, titulo) {
      if (!confirm('Remover a senha "' + titulo + '"? Esta ação não pode ser desfeita.')) return;
      await api("/remover", "POST", { id: id });
      listar();
    }

    async function buscar() {
      const termo = document.getElementById("in-busca").value.trim();
      if (!termo) { listar(); return; }
      const { ok, dados } = await api("/buscar", "POST", { termo: termo });
      if (ok) renderLista(dados.entradas || [], 'Nenhuma senha encontrada para "' + termo + '".');
    }

    async function listar() {
      const { ok, dados } = await api("/listar", "GET");
      if (ok) renderLista(dados.entradas || [], "Nenhuma senha guardada ainda.");
    }

    function renderLista(entradas, vazioTexto) {
      const div = document.getElementById("lista");
      if (!entradas || entradas.length === 0) {
        div.innerHTML = '<div class="vazio">' + (vazioTexto || "Nenhuma senha guardada ainda.") + '</div>';
        return;
      }
      div.innerHTML = "";
      for (const e of entradas) {
        const card = document.createElement("div");
        card.className = "entrada";
        const meta = [e.usuario_servico, e.url].filter(Boolean).join(" · ");
        card.innerHTML =
          '<div class="cab"><div class="tit"></div>' +
          '<div class="ctrl">' +
          '<button class="sec mini" title="Mover para cima">↑</button>' +
          '<button class="sec mini" title="Mover para o topo">Topo</button>' +
          '<button class="sec mini" title="Editar">Editar</button>' +
          '<button class="sec mini perigo" title="Remover">Remover</button>' +
          '</div></div>' +
          (meta ? '<div class="meta"></div>' : '') +
          '<div class="senha"><code>••••••••</code>' +
          '<button class="sec mini">Mostrar</button>' +
          '<button class="sec mini">Copiar</button></div>';
        card.querySelector(".tit").textContent = e.titulo;
        if (meta) card.querySelector(".meta").textContent = meta;
        const ctrl = card.querySelectorAll(".ctrl button");
        ctrl[0].onclick = () => mover(e.id, "cima");
        ctrl[1].onclick = () => mover(e.id, "topo");
        ctrl[2].onclick = () => editar(e);
        ctrl[3].onclick = () => remover(e.id, e.titulo);
        const code = card.querySelector("code");
        const btns = card.querySelectorAll(".senha button");
        let visivel = false;
        btns[0].onclick = () => {
          visivel = !visivel;
          code.textContent = visivel ? e.senha : "••••••••";
          btns[0].textContent = visivel ? "Ocultar" : "Mostrar";
        };
        btns[1].onclick = () => navigator.clipboard.writeText(e.senha);
        div.appendChild(card);
      }
    }
  


// Liga os eventos sem atributos inline (necessario para o CSP estrito).
document.addEventListener("DOMContentLoaded", () => {
  document.getElementById("btn-desbloquear").addEventListener("click", desbloquear);
  document.getElementById("btn-criar").addEventListener("click", criarUsuario);
  document.getElementById("btn-bloquear").addEventListener("click", bloquear);
  document.getElementById("btn-gerar").addEventListener("click", gerarSenha);
  document.getElementById("btn-salvar").addEventListener("click", salvar);
  document.getElementById("btn-cancelar").addEventListener("click", cancelarEdicao);
  document.getElementById("in-busca").addEventListener("input", buscar);
});
