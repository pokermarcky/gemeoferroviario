import os


# Os testes da interface exercitam o orçamento, não o redirecionamento OIDC.
os.environ["RAILPARAMETRIC_TEST_MODE"] = "1"

