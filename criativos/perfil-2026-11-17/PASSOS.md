# Foto de perfil — monograma TB (não aplicar)

Data: 2026-11-17 (America/Fortaleza). Nada foi enviado ao Facebook.

## Onde está a arte

- Editor: https://www.magicpatterns.com/c/oa6jym3ubfzkmwqd4lrydc
- Artefato: prefixo `b4f96dc8` (o UUID completo não está escrito no repo).
- Peça: monograma TB, família do selo (D-009). Cormorant Garamond. Paleta lacre `#3E241C`, pergaminho `#F6EBD8`, ouro `#C9A15B`.
- O usuário já disse “vamos deixar assim”. Não regenerar e não redesenhar.

O PNG **não está** em `criativos/`. Nesta sessão o Magic Patterns não foi chamado: o shell foi recusado e o conector do Cursor (`plugin-magic-patterns`) está sem autenticação. A autenticação que vale é a do mcporter, já feita. Não abrir um login novo.

## Exportar (quando o mcporter responder)

1. Abrir o artefato `b4f96dc8` na conversa `oa6jym3ubfzkmwqd4lrydc`.
2. Exportar só o quadro do monograma TB, PNG quadrado. Não pedir geração nova.
3. Salvar em `criativos/perfil-2026-11-17/monograma-tb.png` (caminho que o script espera).
4. Conferir à vista: letras T e B, grafia TuttiBom, sem preço, sem texto de terceiro.

## Trocar na Página (só na janela do profile-fb)

Não rodar enquanto `fb_agent.py` estiver no ar. O `.parentlock` do perfil estava presente nesta sessão.

```bash
python3 scripts/fb_trocar_foto.py --dry-run
```

Se o dry-run sair 0, a aplicação (ainda precisa do ok do usuário à imagem exata) é:

```bash
python3 scripts/fb_trocar_foto.py
```

O script abre `https://www.facebook.com/profile.php?id=100089750066330`, recusa o perfil pessoal “TuttiBom Novidade”, aceita o nome “TuttiBom” ou, enquanto o Facebook analisa a renomeação, “TutiBom”, e para em checkpoint, login, 2FA ou alerta de bot. Não mata o `fb_agent`.
