import random
import sys
from dataclasses import dataclass

import pygame

LARGURA, ALTURA = 980, 640
FPS = 50
SALAS_ATE_BOSS = 5

COR_FUNDO = (15, 20, 40)
COR_PAINEL = (25, 32, 58)
COR_BORDA = (60, 80, 140)
COR_HEROI = (70, 180, 255)
COR_INIMIGO = (230, 70, 70)
COR_BOSS = (255, 120, 30)
COR_VIDA_BG = (60, 20, 20)
COR_VIDA_OK = (80, 220, 80)
COR_VIDA_MEDIO = (220, 200, 50)
COR_VIDA_BAIXO = (220, 80, 50)
COR_INPUT_BG = (20, 28, 55)
COR_INPUT_BORDA = (100, 140, 255)
COR_TEXTO = (220, 230, 255)
COR_TEXTO_DIM = (130, 150, 200)
COR_ACERTO = (80, 255, 150)
COR_ERRO = (255, 110, 80)
COR_OURO = (255, 200, 50)


@dataclass
class Weapon:
    nome: str
    modo: str


@dataclass
class Challenge:
    tipo: str
    prompt: str
    resposta: int | None
    dano_base: int
    penalidade: int


class Player:

    def __init__(self, hp_max: int = 100):
        self.hp_max = hp_max
        self.hp = hp_max
        self.armas = [
            Weapon("Lamina da Area", "coleta"),
            Weapon("Foice Primitiva", "indefinida"),
            Weapon("Canhao Definido", "definida"),
        ]
        self.arma_idx = 0
        self.metodos = {
            "substituicao": False,
            "partes": False,
        }

    @property
    def arma_atual(self) -> Weapon:
        return self.armas[self.arma_idx]

    @property
    def vivo(self) -> bool:
        return self.hp > 0

    def tomar_dano(self, dano: int):
        self.hp = max(0, self.hp - dano)

    def curar_total(self):
        self.hp = self.hp_max


class MathEngine:

    def valor_polinomio(self, termos: list[tuple[int, int]], x: int) -> int:
        total = 0
        for coef, exp in termos:
            total += coef * (x ** exp)
        return total

    def integral_definida(self, termos: list[tuple[int, int]], a: int, b: int) -> int:
        total = 0
        for coef, exp in termos:
            novo_exp = exp + 1
            total += (coef // novo_exp) * ((b ** novo_exp) - (a ** novo_exp))
        return total

    def derivada_valor(self, termos: list[tuple[int, int]], x: int) -> int:
        total = 0
        for coef, exp in termos:
            if exp > 0:
                total += coef * exp * (x ** (exp - 1))
        return total

    def parsear_digitos(self, texto: str) -> int | None:
        try:
            if not texto.strip():
                return None
            return int(texto)
        except Exception:
            return None


class Enemy:

    def __init__(self, sala: int, boss: bool = False):
        self.sala = sala
        self.boss = boss
        base_hp = 90 + sala * 15
        self.hp_max = max(30, (base_hp + (70 if boss else 0)) // 2)
        self.hp = self.hp_max
        self.armor = 6 + sala * 2 + (8 if boss else 0)
        self.nome = "BOSS INTEGRAL" if boss else f"Inimigo da Sala {sala}"

        self.termos_resistencia: list[tuple[int, int]] = []
        self.display_resistencia = ""

        self.partes_etapa = 0
        self.partes_termos: list[tuple[int, int]] = []
        self.partes_a = 0
        self.partes_b = 1

    @property
    def vivo(self) -> bool:
        return self.hp > 0

    def tomar_dano(self, dano: int):
        self.hp = max(0, self.hp - dano)

    def reduzir_armadura(self, valor: int):
        self.armor = max(0, self.armor - valor)


class InputField:

    def __init__(self, rect: pygame.Rect, fonte: pygame.font.Font, max_len: int = 9):
        self.rect = rect
        self.fonte = fonte
        self.texto = ""
        self.max_len = max_len
        self.permitidos = set("0123456789")

    def handle_event(self, evento: pygame.event.Event):
        if evento.type != pygame.KEYDOWN:
            return None
        if evento.key == pygame.K_BACKSPACE:
            self.texto = self.texto[:-1]
            return None
        if evento.key == pygame.K_RETURN:
            return "submit"
        if evento.unicode in self.permitidos and len(self.texto) < self.max_len:
            self.texto += evento.unicode
        return None

    def limpar(self):
        self.texto = ""

    def desenhar(self, tela):
        pygame.draw.rect(tela, COR_INPUT_BG, self.rect, border_radius=8)
        pygame.draw.rect(tela, COR_INPUT_BORDA, self.rect, 2, border_radius=8)
        surf = self.fonte.render(self.texto, True, COR_TEXTO)
        tela.blit(surf, (self.rect.x + 12, self.rect.y + 10))


def formatar_polinomio(termos: list[tuple[int, int]]) -> str:
    partes = []
    for coef, exp in termos:
        if coef == 0:
            continue
        if exp == 0:
            partes.append(f"{coef}")
        elif exp == 1:
            partes.append("x" if coef == 1 else f"{coef}x")
        else:
            partes.append(f"x^{exp}" if coef == 1 else f"{coef}x^{exp}")
    return " + ".join(partes) if partes else "0"


def desenhar_barra_vida(tela, rect: pygame.Rect, hp: int, hp_max: int, label: str, fonte):
    bx, by, bw, bh = rect
    pct = max(0.0, min(1.0, hp / hp_max))

    if pct > 0.5:
        cor = COR_VIDA_OK
    elif pct > 0.25:
        cor = COR_VIDA_MEDIO
    else:
        cor = COR_VIDA_BAIXO

    pygame.draw.rect(tela, COR_VIDA_BG, rect, border_radius=6)
    fill_w = int(bw * pct)
    if fill_w > 0:
        pygame.draw.rect(tela, cor, (bx, by, fill_w, bh), border_radius=6)
    pygame.draw.rect(tela, COR_BORDA, rect, 2, border_radius=6)

    txt = fonte.render(f"{label}: {hp}/{hp_max} HP", True, COR_TEXTO)
    tela.blit(txt, (bx, by - 20))


class CombatScene:

    def __init__(self, tela, clock):
        self.tela = tela
        self.clock = clock
        self.math = MathEngine()

        self.fonte_titulo = pygame.font.SysFont("consolas", 28, bold=True)
        self.fonte_grande = pygame.font.SysFont("consolas", 21, bold=True)
        self.fonte_media = pygame.font.SysFont("consolas", 17)
        self.fonte_pequena = pygame.font.SysFont("consolas", 14)

        self.overlay_vitoria = self._criar_overlay((10, 30, 10, 180))
        self.overlay_derrota = self._criar_overlay((30, 5, 5, 190))
        self.overlay_final = self._criar_overlay((20, 20, 0, 200))

        self.input_rect = pygame.Rect(250, 520, 480, 44)
        self.input_field = InputField(self.input_rect, self.fonte_grande)

        self.player = Player(100)
        self.sala_atual = 1
        self.enemy = self._gerar_inimigo_da_sala()
        self.challenge = self._gerar_challenge_por_arma()

        self.estado = "combate"
        self.mensagem = "Escolha arma com Q/W/E e responda com ENTER."
        self.cor_mensagem = COR_TEXTO
        self.tempo_msg = 220
        self.ultimo_dano = 0

        self.final_frames = 0
        self.final_reveladas = 0
        self.final_reveal_interval = 50
        self.final_scroll_vel = 0.45
        self.final_horizonte_y = 130
        self.final_linhas = [
            "Depois de varias batalhas arduas no reino do calculo...",
            "o heroi dominou tecnicas, metodos e estrategias.",
            "Substituicao, Integracao por Partes e coragem absoluta.",
            "Nenhuma funcao resistiu ao seu conhecimento.",
            "Hoje, seu nome ecoa entre todas as salas.",
            "Agora ele eh o Rei das Integrais, Pedro Girotto.",
        ]
        self.final_estrelas = [
            (random.randint(0, LARGURA - 1), random.randint(0, ALTURA - 1), random.randint(90, 220))
            for _ in range(120)
        ]
        self.efeitos_ativos: dict[str, int] = {}

    def _criar_overlay(self, cor_rgba):
        overlay = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
        overlay.fill(cor_rgba)
        return overlay

    def _gerar_termos_integraveis(self, grau_max: int = 3, escala: int = 3) -> list[tuple[int, int]]:
        grau = random.randint(1, grau_max)
        termos = []
        for exp in range(grau, -1, -1):
            if exp == 0:
                coef = random.randint(0, 5 + self.sala_atual)
            else:
                coef = random.randint(1, escala + self.sala_atual)
                coef *= (exp + 1)
            termos.append((coef, exp))
        return termos

    def _gerar_inimigo_da_sala(self) -> Enemy:
        boss = self.sala_atual == SALAS_ATE_BOSS
        inimigo = Enemy(self.sala_atual, boss=boss)
        inimigo.termos_resistencia = self._gerar_termos_integraveis(grau_max=3 if boss else 2)
        inimigo.display_resistencia = formatar_polinomio(inimigo.termos_resistencia)
        return inimigo

    def _desbloquear_metodos(self):
        desbloqueado = None
        if self.sala_atual >= 2 and not self.player.metodos["substituicao"]:
            self.player.metodos["substituicao"] = True
            desbloqueado = "substituicao"
        if self.sala_atual >= 3 and not self.player.metodos["partes"]:
            self.player.metodos["partes"] = True
            desbloqueado = "partes"
        return desbloqueado

    def _gerar_challenge_por_arma(self) -> Challenge:
        modo = self.player.arma_atual.modo

        if modo == "coleta":
            total_pedacos = random.randint(20, 60)
            dano = max(4, int(total_pedacos * 0.6))
            prompt = (
                "Nocao de Integral: para completar uma area, quantos pedacos de energia você deve juntar"
                f" se o total eh {total_pedacos}?"
            )
            return Challenge("coleta", prompt, total_pedacos, dano, 4)

        if modo == "indefinida":
            termos = self._gerar_termos_integraveis(grau_max=2, escala=2)
            x_ref = random.randint(1, 3)
            resposta = self.math.integral_definida(termos, 0, x_ref)
            prompt = (
                "Integral Indefinida: encontre F(x) e informe F(" + str(x_ref) + ") assumindo C=0 para f(x)="
                + formatar_polinomio(termos)
            )
            return Challenge("indefinida", prompt, resposta, 22 + self.sala_atual * 2, 9)

        a = random.randint(0, 2 + self.sala_atual // 2)
        b = random.randint(a + 1, a + 3)
        termos = self._gerar_termos_integraveis(grau_max=3 if self.enemy.boss else 2, escala=3)
        resposta = self.math.integral_definida(termos, a, b)
        prompt = (
            "Calcule a integral definida: ("
            + formatar_polinomio(termos)
            + f") dx de {a} ate {b}"
        )
        return Challenge("definida", prompt, resposta, 26 + self.sala_atual * 2, 10)

    def _gerar_challenge_substituicao(self) -> Challenge:
        x_val = random.randint(2, 5)
        coef = random.randint(2, 5)
        k = random.randint(1, 9)
        resposta = coef * x_val + k
        prompt = (
            "Substituicao (quebra de armadura): se u="
            + str(coef)
            + "x+"
            + str(k)
            + ", qual o valor de u quando x="
            + str(x_val)
            + "?"
        )
        return Challenge("substituicao", prompt, resposta, 0, 6)

    def _gerar_challenge_partes(self) -> Challenge:
        if self.enemy.partes_etapa == 0:
            termos = self._gerar_termos_integraveis(grau_max=2, escala=2)
            self.enemy.partes_termos = termos
            self.enemy.partes_etapa = 1
            resposta = self.math.derivada_valor(termos, 1)
            prompt = "Integracao por Partes - Etapa 1/2: calcule d/dx de u em x=1 para u=" + formatar_polinomio(termos)
            return Challenge("partes_etapa1", prompt, resposta, 0, 7)

        a = random.randint(0, 2)
        b = random.randint(a + 1, a + 3)
        self.enemy.partes_a = a
        self.enemy.partes_b = b
        resposta = self.math.integral_definida(self.enemy.partes_termos, a, b)
        prompt = (
            "Integracao por Partes - Etapa 2/2: agora integre u de "
            + str(a)
            + " ate "
            + str(b)
            + " para u="
            + formatar_polinomio(self.enemy.partes_termos)
        )
        return Challenge("partes_etapa2", prompt, resposta, 36 + self.sala_atual * 2, 9)

    def _inimigo_contra_ataca(self, dano_base: int):
        # Dano cresce no fim do jogo para reforcar o risco de erro em inimigos complexos.
        dano = dano_base + self.sala_atual
        self.player.tomar_dano(dano)
        self.ultimo_dano = dano

    def _aplicar_dano_no_inimigo(self, dano: int):
        dano_real = max(1, dano - self.enemy.armor)
        self.enemy.tomar_dano(dano_real)
        self.ultimo_dano = dano_real

    def _ativar_efeito(self, nome: str, duracao: int):
        self.efeitos_ativos[nome] = duracao

    def _atualizar_efeitos(self):
        remover = []
        for nome, tempo in self.efeitos_ativos.items():
            novo = tempo - 1
            if novo <= 0:
                remover.append(nome)
            else:
                self.efeitos_ativos[nome] = novo
        for nome in remover:
            del self.efeitos_ativos[nome]

    def _offset_inimigo(self) -> tuple[int, int]:
        if "substituicao" in self.efeitos_ativos:
            return random.randint(-5, 5), random.randint(-3, 3)
        return 0, 0

    def _desenhar_efeitos(self, ix: int, iy: int):
        if "lamina" in self.efeitos_ativos:
            pygame.draw.line(self.tela, (220, 240, 255), (ix - 25, iy + 72), (ix + 135, iy + 72), 5)

        if "foice" in self.efeitos_ativos:
            pygame.draw.line(self.tela, (255, 255, 210), (ix + 55, iy - 26), (ix + 55, iy + 78), 5)
            pygame.draw.line(self.tela, (255, 220, 180), (ix + 28, iy + 4), (ix + 82, iy + 22), 3)

        if "canhao" in self.efeitos_ativos:
            pygame.draw.circle(self.tela, (255, 230, 180), (ix + 126, iy + 72), 26)
            pygame.draw.circle(self.tela, (255, 140, 80), (ix + 126, iy + 72), 14)
            pygame.draw.circle(self.tela, (255, 255, 210), (ix + 60, iy + 72), 6)

        if "partes" in self.efeitos_ativos:
            pygame.draw.line(self.tela, (220, 255, 220), (ix - 20, iy + 98), (ix + 130, iy + 48), 4)
            pygame.draw.line(self.tela, (220, 255, 220), (ix + 55, iy - 20), (ix + 55, iy + 120), 4)

        if "substituicao" in self.efeitos_ativos:
            tempo = self.efeitos_ativos["substituicao"]
            fase = tempo % 18
            for raio, cor in ((30, (180, 120, 255)), (42, (140, 220, 255))):
                x = ix + 55 + int((raio - 18) * 0.6 * (1 if fase < 9 else -1))
                y = iy + 50 + int((fase - 9) * 0.7)
                pygame.draw.circle(self.tela, cor, (x, y), 5)

    def _avaliar_resposta(self):
        valor = self.math.parsear_digitos(self.input_field.texto)
        self.input_field.limpar()

        if valor is None:
            self.mensagem = "Resposta invalida. Use apenas digitos."
            self.cor_mensagem = COR_ERRO
            self.tempo_msg = 170
            return

        ch = self.challenge

        if ch.tipo == "coleta":
            total = ch.resposta if ch.resposta is not None else 0
            if valor == total:
                self._aplicar_dano_no_inimigo(ch.dano_base)
                self._ativar_efeito("lamina", 10)
                self.mensagem = f"Area completa! Dano maximo: {self.ultimo_dano}."
                self.cor_mensagem = COR_ACERTO
            else:
                self._inimigo_contra_ataca(ch.penalidade)
                self.mensagem = "Coleta errada: quantidade incorreta de energia."
                self.cor_mensagem = COR_ERRO
            self.tempo_msg = 190

        elif ch.tipo == "substituicao":
            if valor == ch.resposta:
                quebra = 8 + self.sala_atual * 2
                self.enemy.reduzir_armadura(quebra)
                self._ativar_efeito("substituicao", 22)
                self.mensagem = f"Substituição feita, Fraqueza encontrada! -{quebra} de defesa."
                self.cor_mensagem = COR_ACERTO
                self.tempo_msg = 180
            else:
                self._inimigo_contra_ataca(ch.penalidade)
                self.mensagem = "Substituicao errada: perdeu o turno e a defesa nao baixou."
                self.cor_mensagem = COR_ERRO
                self.tempo_msg = 210

        elif ch.tipo == "partes_etapa1":
            if valor == ch.resposta:
                self.challenge = self._gerar_challenge_partes()
                self.mensagem = "Etapa 1 correta. Falta integrar para concluir o golpe!"
                self.cor_mensagem = COR_ACERTO
                self.tempo_msg = 170
                return
            self.enemy.partes_etapa = 0
            self._inimigo_contra_ataca(ch.penalidade)
            self.mensagem = "Erro na derivacao. Combo por partes cancelado."
            self.cor_mensagem = COR_ERRO
            self.tempo_msg = 180

        elif ch.tipo == "partes_etapa2":
            if valor == ch.resposta:
                self._aplicar_dano_no_inimigo(ch.dano_base)
                self._ativar_efeito("partes", 12)
                self.mensagem = f"Combo por partes completo! {self.ultimo_dano} de dano."
                self.cor_mensagem = COR_ACERTO
                self.tempo_msg = 190
            else:
                self._inimigo_contra_ataca(ch.penalidade)
                self.mensagem = "Falha na etapa final por partes."
                self.cor_mensagem = COR_ERRO
                self.tempo_msg = 190
            self.enemy.partes_etapa = 0

        else:
            if valor == ch.resposta:
                self._aplicar_dano_no_inimigo(ch.dano_base)
                if ch.tipo == "indefinida":
                    self._ativar_efeito("foice", 10)
                else:
                    self._ativar_efeito("canhao", 12)
                self.mensagem = f"Acertou! {self.ultimo_dano} de dano."
                self.cor_mensagem = COR_ACERTO
                self.tempo_msg = 180
            else:
                if ch.tipo == "indefinida":
                    # Regra: erro na indefinida reflete metade do dano no heroi.
                    self._inimigo_contra_ataca(max(1, ch.dano_base // 2))
                    self.mensagem = "Indefinida errada: arma falhou e voce sofreu metade do dano."
                else:
                    self._inimigo_contra_ataca(ch.penalidade)
                    self.mensagem = "Integral errada: o inimigo puniu seu turno."
                self.cor_mensagem = COR_ERRO
                self.tempo_msg = 210

        if not self.enemy.vivo:
            self.estado = "vitoria"
            return

        if not self.player.vivo:
            self.estado = "derrota"
            return

        self.challenge = self._gerar_challenge_por_arma()

    def _avancar_sala(self):
        if self.sala_atual >= SALAS_ATE_BOSS:
            self.estado = "fim"
            return

        self.sala_atual += 1
        metodos_desbloqueados = self._desbloquear_metodos()
        self.enemy = self._gerar_inimigo_da_sala()
        self.challenge = self._gerar_challenge_por_arma()
        self.estado = "combate"
        self.mensagem = f"Sala {self.sala_atual}! Novo desafio encontrado."
        self.cor_mensagem = COR_OURO
        self.tempo_msg = 180
        
        if metodos_desbloqueados == "substituicao":
            cap_sub = CapituloSubstituicao(self.tela, self.clock)
            cap_sub.rodar()
        elif metodos_desbloqueados == "partes":
            cap_partes = CapituloPartes(self.tela, self.clock)
            cap_partes.rodar()

    def reiniciar_partida(self):
        self.player = Player(100)
        self.sala_atual = 1
        self.enemy = self._gerar_inimigo_da_sala()
        self.challenge = self._gerar_challenge_por_arma()
        self.estado = "combate"
        self.mensagem = "Nova partida iniciada."
        self.cor_mensagem = COR_TEXTO
        self.tempo_msg = 140
        self.ultimo_dano = 0
        self.input_field.limpar()

    def _selecionar_arma(self, idx: int):
        if 0 <= idx < len(self.player.armas):
            self.player.arma_idx = idx
            self.enemy.partes_etapa = 0
            self.challenge = self._gerar_challenge_por_arma()
            self.mensagem = f"Arma equipada: {self.player.arma_atual.nome}"
            self.cor_mensagem = COR_OURO
            self.tempo_msg = 120

    def _usar_substituicao(self):
        if not self.player.metodos["substituicao"]:
            self.mensagem = "Metodo de substituicao ainda nao desbloqueado."
            self.cor_mensagem = COR_ERRO
            self.tempo_msg = 150
            return
        self.enemy.partes_etapa = 0
        self.challenge = self._gerar_challenge_substituicao()
        self.mensagem = "Substituicao ativa: responda para quebrar armadura."
        self.cor_mensagem = COR_OURO
        self.tempo_msg = 130

    def _usar_partes(self):
        if not self.player.metodos["partes"]:
            self.mensagem = "Integracao por partes ainda nao desbloqueada."
            self.cor_mensagem = COR_ERRO
            self.tempo_msg = 150
            return
        self.challenge = self._gerar_challenge_partes()
        self.mensagem = "Combo por partes iniciado."
        self.cor_mensagem = COR_OURO
        self.tempo_msg = 130

    def _atalho_dev_pular_fase(self):
        self.mensagem = "DEV: fase concluida com sucesso."
        self.cor_mensagem = COR_ACERTO
        self.tempo_msg = 120
        self._avancar_sala()

    def _atalho_dev_finalizar(self):
        self.estado = "fim"
        self.mensagem = "DEV: salto para tela final."
        self.cor_mensagem = COR_OURO
        self.tempo_msg = 120

    def rodar(self):
        rodando = True
        while rodando:
            self.clock.tick(FPS)
            self._atualizar_efeitos()

            for evento in pygame.event.get():
                if evento.type == pygame.QUIT:
                    rodando = False

                if self.estado == "combate" and evento.type == pygame.KEYDOWN:
                    if evento.key == pygame.K_ESCAPE:
                        rodando = False
                    elif evento.key == pygame.K_q:
                        self._selecionar_arma(0)
                    elif evento.key == pygame.K_w:
                        self._selecionar_arma(1)
                    elif evento.key == pygame.K_e:
                        self._selecionar_arma(2)
                    elif evento.key == pygame.K_r:
                        self._usar_substituicao()
                    elif evento.key == pygame.K_t:
                        self._usar_partes()
                    elif evento.key == pygame.K_p:
                        self._atalho_dev_pular_fase()
                    elif evento.key == pygame.K_g:
                        self._atalho_dev_finalizar()
                    else:
                        acao = self.input_field.handle_event(evento)
                        if acao == "submit" and self.input_field.texto.strip():
                            self._avaliar_resposta()

                elif self.estado in ("vitoria", "derrota", "fim") and evento.type == pygame.KEYDOWN:
                    if self.estado == "vitoria":
                        self._avancar_sala()
                    elif self.estado == "derrota":
                        self.reiniciar_partida()
                    else:
                        if self.final_reveladas >= len(self.final_linhas):
                            rodando = False

            if self.tempo_msg > 0:
                self.tempo_msg -= 1

            if self.estado == "fim":
                self.final_frames += 1
                if (
                    self.final_reveladas < len(self.final_linhas)
                    and self.final_frames % self.final_reveal_interval == 0
                ):
                    self.final_reveladas += 1

            self.tela.fill(COR_FUNDO)
            self._desenhar_combate()

            if self.estado == "vitoria":
                self._desenhar_overlay_vitoria()
            elif self.estado == "derrota":
                self._desenhar_overlay_derrota()
            elif self.estado == "fim":
                self._desenhar_overlay_final()

            pygame.display.flip()

        pygame.quit()
        sys.exit()

    def _desenhar_combate(self):
        titulo = self.fonte_titulo.render(
            f"INTEGRAL QUEST | Sala {self.sala_atual}/{SALAS_ATE_BOSS}",
            True,
            COR_OURO,
        )
        self.tela.blit(titulo, (LARGURA // 2 - titulo.get_width() // 2, 14))

        hx, hy = 70, 160
        pygame.draw.rect(self.tela, COR_HEROI, (hx, hy, 110, 145), border_radius=8)
        pygame.draw.rect(self.tela, (150, 220, 255), (hx, hy, 110, 145), 3, border_radius=8)
        label_h = self.fonte_media.render("HEROI", True, COR_HEROI)
        self.tela.blit(label_h, (hx + 55 - label_h.get_width() // 2, hy + 52))
        self.tela.blit(self.fonte_grande.render("[H]", True, (200, 240, 255)), (hx + 37, hy + 78))

        cor_inimigo = COR_BOSS if self.enemy.boss else COR_INIMIGO
        ix_base, iy_base = 800, 160
        dx, dy = self._offset_inimigo()
        ix, iy = ix_base + dx, iy_base + dy
        pygame.draw.rect(self.tela, cor_inimigo, (ix, iy, 110, 145), border_radius=8)
        pygame.draw.rect(self.tela, (255, 170, 120), (ix, iy, 110, 145), 3, border_radius=8)
        nome_i = "BOSS" if self.enemy.boss else "INIMIGO"
        label_i = self.fonte_media.render(nome_i, True, cor_inimigo)
        self.tela.blit(label_i, (ix + 55 - label_i.get_width() // 2, iy + 52))
        self.tela.blit(self.fonte_grande.render("[I]", True, (255, 200, 160)), (ix + 37, iy + 78))
        self._desenhar_efeitos(ix, iy)

        desenhar_barra_vida(self.tela, pygame.Rect(65, 125, 180, 14), self.player.hp, self.player.hp_max, "HP Heroi", self.fonte_pequena)
        desenhar_barra_vida(
            self.tela,
            pygame.Rect(740, 125, 210, 14),
            self.enemy.hp,
            self.enemy.hp_max,
            "HP Inimigo",
            self.fonte_pequena,
        )

        armadura_txt = self.fonte_pequena.render(f"Defesa inimiga: {self.enemy.armor}", True, COR_TEXTO_DIM)
        self.tela.blit(armadura_txt, (745, 146))

        painel_y = 325
        pygame.draw.rect(self.tela, COR_PAINEL, (34, painel_y, LARGURA - 68, 282), border_radius=10)
        pygame.draw.rect(self.tela, COR_BORDA, (34, painel_y, LARGURA - 68, 282), 2, border_radius=10)

        linhas_desafio = self._quebrar_texto(self.challenge.prompt, self.fonte_media, LARGURA - 120)
        for i, linha in enumerate(linhas_desafio[:3]):
            surf = self.fonte_media.render(linha, True, COR_OURO)
            self.tela.blit(surf, (50, painel_y + 18 + i * 22))

        dica = "Dica: definida = F(b)-F(a) | R = Substituicao | T= Integral por partes"
        self.tela.blit(self.fonte_pequena.render(dica, True, COR_TEXTO_DIM), (50, painel_y + 74))

        armas = (
            f"Arma atual: {self.player.arma_atual.nome} | "
            "Q-Lamina da Area  W-Foice Primitiva  E-Canhao Definido"
        )
        self.tela.blit(self.fonte_pequena.render(armas, True, COR_TEXTO), (50, painel_y + 100))

        met = (
            "Metodos: "
            f"R-Substituicao [{'OK' if self.player.metodos['substituicao'] else 'BLOQ'}] | "
            f"T-Partes [{'OK' if self.player.metodos['partes'] else 'BLOQ'}]"
        )
        self.tela.blit(self.fonte_pequena.render(met, True, COR_TEXTO), (50, painel_y + 120))

        if self.mensagem and self.tempo_msg > 0:
            msg = self.fonte_media.render(self.mensagem, True, self.cor_mensagem)
            self.tela.blit(msg, (50, painel_y + 148))

        lbl = self.fonte_pequena.render("Resposta numerica (digitos) e ENTER para confirmar:", True, COR_TEXTO_DIM)
        self.tela.blit(lbl, (self.input_rect.x, self.input_rect.y - 20))
        self.input_field.desenhar(self.tela)

        ajuda = "ESC: sair | Acertar = dano | Errar = punicao"
        self.tela.blit(self.fonte_pequena.render(ajuda, True, COR_TEXTO_DIM), (LARGURA // 2 - 170, ALTURA - 24))

    def _quebrar_texto(self, texto: str, fonte: pygame.font.Font, largura_max: int) -> list[str]:
        palavras = texto.split()
        if not palavras:
            return [""]

        linhas = []
        linha_atual = palavras[0]

        for palavra in palavras[1:]:
            candidata = f"{linha_atual} {palavra}"
            if fonte.size(candidata)[0] <= largura_max:
                linha_atual = candidata
            else:
                linhas.append(linha_atual)
                linha_atual = palavra

        linhas.append(linha_atual)
        return linhas

    def _desenhar_texto_centralizado(self, texto, fonte, cor, y):
        surf = fonte.render(texto, True, cor)
        self.tela.blit(surf, (LARGURA // 2 - surf.get_width() // 2, y))

    def _desenhar_overlay_vitoria(self):
        self.tela.blit(self.overlay_vitoria, (0, 0))
        self._desenhar_texto_centralizado("INIMIGO DERROTADO!", self.fonte_titulo, COR_ACERTO, 215)
        self._desenhar_texto_centralizado(f"{self.ultimo_dano} de dano!", self.fonte_grande, COR_OURO, 265)
        if self.sala_atual < SALAS_ATE_BOSS:
            self._desenhar_texto_centralizado("Pressione qualquer tecla para a proxima sala...", self.fonte_media, COR_TEXTO_DIM, 315)
        else:
            self._desenhar_texto_centralizado("Boss integrado por completo!", self.fonte_media, COR_TEXTO_DIM, 315)

    def _desenhar_overlay_derrota(self):
        self.tela.blit(self.overlay_derrota, (0, 0))
        self._desenhar_texto_centralizado("HEROI DERROTADO!", self.fonte_titulo, COR_ERRO, 210)
        self._desenhar_texto_centralizado("Nao desista! A pratica leva a perfeicao.", self.fonte_grande, COR_OURO, 260)
        self._desenhar_texto_centralizado("Pressione qualquer tecla para recomecar...", self.fonte_media, COR_TEXTO_DIM, 310)

    def _desenhar_overlay_final(self):
        self.tela.fill((4, 6, 16))
        self._desenhar_estrelas_final()

        titulo = self.fonte_titulo.render("CAPITULO FINAL - CONCLUSAO", True, COR_OURO)
        self.tela.blit(titulo, (LARGURA // 2 - titulo.get_width() // 2, 34))

        scroll = self.final_frames * self.final_scroll_vel
        inicio_y = ALTURA + 40

        for i in range(self.final_reveladas):
            y = inicio_y + i * 44 - scroll
            if -80 <= y <= ALTURA + 50:
                self._desenhar_linha_crawl_final(self.final_linhas[i], y)

        if self.final_reveladas >= len(self.final_linhas):
            y_ultima = inicio_y + (len(self.final_linhas) - 1) * 44 - scroll
            if ALTURA // 2 - 50 <= y_ultima <= ALTURA // 2 + 50:
                aviso = self.fonte_pequena.render("Pressione qualquer tecla para sair.", True, COR_TEXTO_DIM)
                self.tela.blit(aviso, (LARGURA // 2 - aviso.get_width() // 2, ALTURA - 30))

    def _desenhar_estrelas_final(self):
        for x, y, brilho in self.final_estrelas:
            self.tela.fill((brilho, brilho, brilho), (x, y, 2, 2))

    def _desenhar_linha_crawl_final(self, texto: str, y: float):
        base = self.fonte_grande.render(texto, True, COR_OURO)

        faixa = ALTURA - self.final_horizonte_y
        t = (y - self.final_horizonte_y) / max(1, faixa)
        t = max(0.0, min(1.0, t))

        escala = 0.32 + 0.88 * t
        nova_largura = max(2, int(base.get_width() * escala))
        nova_altura = max(2, int(base.get_height() * escala))
        linha = pygame.transform.smoothscale(base, (nova_largura, nova_altura))

        alpha = int(70 + 185 * t)
        linha.set_alpha(alpha)

        x = LARGURA // 2 - linha.get_width() // 2
        self.tela.blit(linha, (x, int(y)))


class IntroScene:

    def __init__(self, tela, clock):
        self.tela = tela
        self.clock = clock
        self.fonte_titulo = pygame.font.SysFont("consolas", 34, bold=True)
        self.fonte_texto = pygame.font.SysFont("consolas", 22, bold=True)
        self.fonte_rodape = pygame.font.SysFont("consolas", 16)

        self.linhas = [
            "Em um reino onde numeros moldam o destino...",
            "um jovem heroi inicia sua jornada no CALCULO.",
            "Cada integral vencida revela um novo poder.",
            "Cada erro cobra um preco em batalha.",
            "Ao acumular conhecimentos e ferramentas,",
            "ele aprendera Substituicao e Integracao por Partes.",
            "Seu destino final: derrotar o Boss Integral.",
            "Somente assim dominara a arte de integrar.",
        ]

        self.estrelas = [
            (random.randint(0, LARGURA - 1), random.randint(0, ALTURA - 1), random.randint(90, 220))
            for _ in range(120)
        ]

        self.frames = 0
        self.reveladas = 0
        self.reveal_interval = 50
        self.scroll_vel = 0.45
        self.horizonte_y = 130

    def rodar(self):
        rodando = True
        while rodando:
            self.clock.tick(FPS)
            self.frames += 1

            if self.reveladas < len(self.linhas) and self.frames % self.reveal_interval == 0:
                self.reveladas += 1

            for evento in pygame.event.get():
                if evento.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if evento.type == pygame.KEYDOWN and evento.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_ESCAPE):
                    if self.reveladas >= len(self.linhas):
                        y_ultima = ALTURA + 40 + (len(self.linhas) - 1) * 44 - self.frames * self.scroll_vel
                        if y_ultima <= ALTURA * 0.75:
                            rodando = False

            self.tela.fill((4, 6, 16))
            self._desenhar_estrelas()

            titulo = self.fonte_titulo.render("CAPITULO I - O DESPERTAR DAS INTEGRAIS", True, COR_OURO)
            self.tela.blit(titulo, (LARGURA // 2 - titulo.get_width() // 2, 34))

            scroll = self.frames * self.scroll_vel
            inicio_y = ALTURA + 40

            for i in range(self.reveladas):
                y = inicio_y + i * 44 - scroll
                if -80 <= y <= ALTURA + 50:
                    self._desenhar_linha_crawl(self.linhas[i], y)

            if self.reveladas >= len(self.linhas):
                y_ultima = inicio_y + (len(self.linhas) - 1) * 44 - scroll
                if y_ultima <= ALTURA * 0.75:
                    aviso = self.fonte_rodape.render("ENTER/ESPACO para iniciar a batalha", True, COR_TEXTO_DIM)
                    self.tela.blit(aviso, (LARGURA // 2 - aviso.get_width() // 2, ALTURA - 32))

            pygame.display.flip()

    def _desenhar_estrelas(self):
        for x, y, brilho in self.estrelas:
            self.tela.fill((brilho, brilho, brilho), (x, y, 2, 2))

    def _desenhar_linha_crawl(self, texto: str, y: float):
        base = self.fonte_texto.render(texto, True, COR_OURO)

        faixa = ALTURA - self.horizonte_y
        t = (y - self.horizonte_y) / max(1, faixa)
        t = max(0.0, min(1.0, t))

        # Perto do "horizonte" a linha fica menor, gerando perspectiva.
        escala = 0.32 + 0.88 * t
        nova_largura = max(2, int(base.get_width() * escala))
        nova_altura = max(2, int(base.get_height() * escala))
        linha = pygame.transform.smoothscale(base, (nova_largura, nova_altura))

        alpha = int(70 + 185 * t)
        linha.set_alpha(alpha)

        x = LARGURA // 2 - linha.get_width() // 2
        self.tela.blit(linha, (x, int(y)))


class CapituloSubstituicao:

    def __init__(self, tela, clock):
        self.tela = tela
        self.clock = clock
        self.fonte_titulo = pygame.font.SysFont("consolas", 34, bold=True)
        self.fonte_texto = pygame.font.SysFont("consolas", 22, bold=True)
        self.fonte_rodape = pygame.font.SysFont("consolas", 16)

        self.linhas = [
            "Uma nova tecnica revela-se ao heroi...",
            "A SUBSTITUICAO: uma maneira de quebrar as defesas inimigas.",
            "Ao compreender como trocas de variaveis simplificam integrais,",
            "ele aprendera a explorar pontos fracos no inimigo.",
            "Sua armadura agora pode ser reduzida significativamente!",
        ]

        self.estrelas = [
            (random.randint(0, LARGURA - 1), random.randint(0, ALTURA - 1), random.randint(90, 220))
            for _ in range(120)
        ]

        self.frames = 0
        self.reveladas = 0
        self.reveal_interval = 35
        self.scroll_vel = 0.6
        self.horizonte_y = 130

    def rodar(self):
        rodando = True
        while rodando:
            self.clock.tick(FPS)
            self.frames += 1

            if self.reveladas < len(self.linhas) and self.frames % self.reveal_interval == 0:
                self.reveladas += 1

            for evento in pygame.event.get():
                if evento.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if evento.type == pygame.KEYDOWN and evento.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_ESCAPE):
                    if self.reveladas >= len(self.linhas):
                        y_ultima = ALTURA + 40 + (len(self.linhas) - 1) * 44 - self.frames * self.scroll_vel
                        if y_ultima <= ALTURA * 0.75:
                            rodando = False

            self.tela.fill((4, 6, 16))
            self._desenhar_estrelas()

            titulo = self.fonte_titulo.render("CAPITULO II - SUBSTITUICAO", True, COR_OURO)
            self.tela.blit(titulo, (LARGURA // 2 - titulo.get_width() // 2, 34))

            scroll = self.frames * self.scroll_vel
            inicio_y = ALTURA + 40

            for i in range(self.reveladas):
                y = inicio_y + i * 44 - scroll
                if -80 <= y <= ALTURA + 50:
                    self._desenhar_linha_crawl(self.linhas[i], y)

            if self.reveladas >= len(self.linhas):
                y_ultima = inicio_y + (len(self.linhas) - 1) * 44 - scroll
                if y_ultima <= ALTURA * 0.75:
                    aviso = self.fonte_rodape.render("ENTER/ESPACO para continuar", True, COR_TEXTO_DIM)
                    self.tela.blit(aviso, (LARGURA // 2 - aviso.get_width() // 2, ALTURA - 32))

            pygame.display.flip()

    def _desenhar_estrelas(self):
        for x, y, brilho in self.estrelas:
            self.tela.fill((brilho, brilho, brilho), (x, y, 2, 2))

    def _desenhar_linha_crawl(self, texto: str, y: float):
        base = self.fonte_texto.render(texto, True, COR_OURO)

        faixa = ALTURA - self.horizonte_y
        t = (y - self.horizonte_y) / max(1, faixa)
        t = max(0.0, min(1.0, t))

        escala = 0.32 + 0.88 * t
        nova_largura = max(2, int(base.get_width() * escala))
        nova_altura = max(2, int(base.get_height() * escala))
        linha = pygame.transform.smoothscale(base, (nova_largura, nova_altura))

        alpha = int(70 + 185 * t)
        linha.set_alpha(alpha)

        x = LARGURA // 2 - linha.get_width() // 2
        self.tela.blit(linha, (x, int(y)))


class CapituloPartes:

    def __init__(self, tela, clock):
        self.tela = tela
        self.clock = clock
        self.fonte_titulo = pygame.font.SysFont("consolas", 34, bold=True)
        self.fonte_texto = pygame.font.SysFont("consolas", 22, bold=True)
        self.fonte_rodape = pygame.font.SysFont("consolas", 16)

        self.linhas = [
            "A jornada avanca, e uma nova estrategia emerge...",
            "INTEGRACAO POR PARTES: a tecnica definitiva para ataques poderosos.",
            "Dividindo o problema em etapas, o heroi compreende estruturas complexas.",
            "Nenhuma integral, por mais intrincada, resiste a esse conhecimento profundo.",
            "Seu ataque agora pode infligir dano massivo quando executado perfeitamente!",
        ]

        self.estrelas = [
            (random.randint(0, LARGURA - 1), random.randint(0, ALTURA - 1), random.randint(90, 220))
            for _ in range(120)
        ]

        self.frames = 0
        self.reveladas = 0
        self.reveal_interval = 35
        self.scroll_vel = 0.6
        self.horizonte_y = 130

    def rodar(self):
        rodando = True
        while rodando:
            self.clock.tick(FPS)
            self.frames += 1

            if self.reveladas < len(self.linhas) and self.frames % self.reveal_interval == 0:
                self.reveladas += 1

            for evento in pygame.event.get():
                if evento.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if evento.type == pygame.KEYDOWN and evento.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_ESCAPE):
                    if self.reveladas >= len(self.linhas):
                        y_ultima = ALTURA + 40 + (len(self.linhas) - 1) * 44 - self.frames * self.scroll_vel
                        if y_ultima <= ALTURA * 0.75:
                            rodando = False

            self.tela.fill((4, 6, 16))
            self._desenhar_estrelas()

            titulo = self.fonte_titulo.render("CAPITULO III - INTEGRACAO POR PARTES", True, COR_OURO)
            self.tela.blit(titulo, (LARGURA // 2 - titulo.get_width() // 2, 34))

            scroll = self.frames * self.scroll_vel
            inicio_y = ALTURA + 40

            for i in range(self.reveladas):
                y = inicio_y + i * 44 - scroll
                if -80 <= y <= ALTURA + 50:
                    self._desenhar_linha_crawl(self.linhas[i], y)

            if self.reveladas >= len(self.linhas):
                y_ultima = inicio_y + (len(self.linhas) - 1) * 44 - scroll
                if y_ultima <= ALTURA * 0.75:
                    aviso = self.fonte_rodape.render("ENTER/ESPACO para continuar", True, COR_TEXTO_DIM)
                    self.tela.blit(aviso, (LARGURA // 2 - aviso.get_width() // 2, ALTURA - 32))

            pygame.display.flip()

    def _desenhar_estrelas(self):
        for x, y, brilho in self.estrelas:
            self.tela.fill((brilho, brilho, brilho), (x, y, 2, 2))

    def _desenhar_linha_crawl(self, texto: str, y: float):
        base = self.fonte_texto.render(texto, True, COR_OURO)

        faixa = ALTURA - self.horizonte_y
        t = (y - self.horizonte_y) / max(1, faixa)
        t = max(0.0, min(1.0, t))

        escala = 0.32 + 0.88 * t
        nova_largura = max(2, int(base.get_width() * escala))
        nova_altura = max(2, int(base.get_height() * escala))
        linha = pygame.transform.smoothscale(base, (nova_largura, nova_altura))

        alpha = int(70 + 185 * t)
        linha.set_alpha(alpha)

        x = LARGURA // 2 - linha.get_width() // 2
        self.tela.blit(linha, (x, int(y)))


class Menu:

    def __init__(self, tela, clock):
        self.tela = tela
        self.clock = clock
        self.fonte_titulo = pygame.font.SysFont("consolas", 38, bold=True)
        self.fonte_botao = pygame.font.SysFont("consolas", 22, bold=True)

        btn_w, btn_h = 240, 56
        cx = LARGURA // 2
        self.rect_jogar = pygame.Rect(cx - btn_w // 2, 250, btn_w, btn_h)
        self.rect_info = pygame.Rect(cx - btn_w // 2, 325, btn_w, btn_h)
        self.rect_sair = pygame.Rect(cx - btn_w // 2, 400, btn_w, btn_h)

    def _desenhar_botao(self, rect, texto, hover):
        cor_fundo = (40, 55, 110) if hover else (25, 35, 72)
        cor_borda = (140, 170, 255) if hover else COR_BORDA
        cor_texto = (255, 255, 255) if hover else COR_TEXTO_DIM
        pygame.draw.rect(self.tela, cor_fundo, rect, border_radius=8)
        pygame.draw.rect(self.tela, cor_borda, rect, 2, border_radius=8)
        surf = self.fonte_botao.render(texto, True, cor_texto)
        self.tela.blit(surf, (rect.centerx - surf.get_width() // 2, rect.centery - surf.get_height() // 2))

    def rodar(self):
        while True:
            self.clock.tick(FPS)
            mouse = pygame.mouse.get_pos()

            for evento in pygame.event.get():
                if evento.type == pygame.QUIT:
                    self._encerrar()
                if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                    if self.rect_jogar.collidepoint(mouse):
                        return "jogar"
                    if self.rect_info.collidepoint(mouse):
                        return "info"
                    if self.rect_sair.collidepoint(mouse):
                        self._encerrar()

            self.tela.fill(COR_FUNDO)
            titulo = self.fonte_titulo.render("SLAY THE INTEGRAL", True, COR_OURO)
            self.tela.blit(titulo, (LARGURA // 2 - titulo.get_width() // 2, 160))

            subt = pygame.font.SysFont("consolas", 16).render("A SERIOUS GAME PRODUCTION", True, COR_TEXTO_DIM)
            self.tela.blit(subt, (LARGURA // 2 - subt.get_width() // 2, 205))

            self._desenhar_botao(self.rect_jogar, "JOGAR", self.rect_jogar.collidepoint(mouse))
            self._desenhar_botao(self.rect_info, "INFORMACOES", self.rect_info.collidepoint(mouse))
            self._desenhar_botao(self.rect_sair, "SAIR", self.rect_sair.collidepoint(mouse))
            pygame.display.flip()

    def _encerrar(self):
        self.tela.fill(COR_FUNDO)
        fonte = pygame.font.SysFont("consolas", 26, bold=True)
        surf = fonte.render("Ate logo!", True, COR_OURO)
        self.tela.blit(surf, (LARGURA // 2 - surf.get_width() // 2, ALTURA // 2 - surf.get_height() // 2))
        pygame.display.flip()
        pygame.time.wait(900)
        pygame.quit()
        sys.exit()


class InfoScene:

    def __init__(self, tela, clock):
        self.tela = tela
        self.clock = clock
        self.fonte_titulo = pygame.font.SysFont("consolas", 34, bold=True)
        self.fonte_texto = pygame.font.SysFont("consolas", 21)
        self.fonte_pequena = pygame.font.SysFont("consolas", 16)

    def rodar(self):
        rodando = True
        while rodando:
            self.clock.tick(FPS)

            for evento in pygame.event.get():
                if evento.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if evento.type == pygame.KEYDOWN and evento.key in (pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_SPACE):
                    rodando = False

            self.tela.fill(COR_FUNDO)
            pygame.draw.rect(self.tela, COR_PAINEL, (90, 90, LARGURA - 180, ALTURA - 180), border_radius=12)
            pygame.draw.rect(self.tela, COR_BORDA, (90, 90, LARGURA - 180, ALTURA - 180), 2, border_radius=12)

            titulo = self.fonte_titulo.render("INFORMACOES", True, COR_OURO)
            self.tela.blit(titulo, (LARGURA // 2 - titulo.get_width() // 2, 130))

            l1 = self.fonte_texto.render("Nomes dos criadores do jogo:", True, COR_TEXTO)
            l2 = self.fonte_texto.render("Gabriel Albuquerque, Davi Maciel e Alberto Acosta", True, COR_TEXTO_DIM)
            l3 = self.fonte_texto.render("Botao de dev: P", True, COR_TEXTO)
            l4 = self.fonte_texto.render("Finalizar o jogo: G", True, COR_TEXTO)
            l5 = self.fonte_pequena.render("Atalhos funcionam durante a batalha.", True, COR_TEXTO_DIM)
            l6 = self.fonte_pequena.render("ESC/ENTER/ESPACO para voltar ao menu", True, COR_TEXTO_DIM)

            self.tela.blit(l1, (140, 220))
            self.tela.blit(l2, (140, 255))
            self.tela.blit(l3, (140, 315))
            self.tela.blit(l4, (140, 348))
            self.tela.blit(l5, (140, 392))
            self.tela.blit(l6, (140, 425))

            pygame.display.flip()


if __name__ == "__main__":
    random.seed()
    pygame.init()
    tela = pygame.display.set_mode((LARGURA, ALTURA), pygame.FULLSCREEN)
    clock = pygame.time.Clock()
    pygame.display.set_caption("Integral Quest - Roguelike de Turnos")

    menu = Menu(tela, clock)
    while True:
        opcao = menu.rodar()
        if opcao == "jogar":
            break
        if opcao == "info":
            info = InfoScene(tela, clock)
            info.rodar()

    intro = IntroScene(tela, clock)
    intro.rodar()

    jogo = CombatScene(tela, clock)
    jogo.rodar()
