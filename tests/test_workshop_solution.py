import unittest

from workshop.checkpoints import CHECKS


class WorkshopSolutionTests(unittest.IsolatedAsyncioTestCase):
    async def test_solution_passes_every_lab(self) -> None:
        for lab, check in CHECKS.items():
            with self.subTest(lab=lab):
                await check("workshop.solution")


if __name__ == "__main__":
    unittest.main()
