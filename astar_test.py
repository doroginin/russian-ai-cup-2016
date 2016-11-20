import astar as pf

import unittest


class Test(unittest.TestCase):

    def setUp(self):
        pass

    def test_maze(self):
        a = pf.AStar()
        walls = ((0, 5), (1, 0), (1, 1), (1, 5), (2, 3),
                 (3, 1), (3, 2), (3, 5), (4, 1), (4, 4), (5, 1))
        a.init_grid(6, 6, walls, (0, 0), (5, 5))

        world = [[" "] * 6 for _ in range(6)]
        for w in walls:
            world[w[0]][w[1]] = '#'

        path = a.solve()

        for p in path:
            world[p[0]][p[1]] = '.'

        for r in world:
            for c in r:
                print(c, end="")
            print()

        self.assertEqual(path, [(0, 0), (0, 1), (0, 2), (1, 2), (1, 3), (1, 4),
                                (2, 4), (3, 4), (3, 3), (4, 3), (5, 3), (5, 4),
                                (5, 5)])

    def test_maze_no_walls(self):
        a = pf.AStar()
        walls = ()
        a.init_grid(6, 6, walls, (0, 0), (5, 5))
        path = a.solve()
        self.assertEqual(len(path), 11)

    def test_maze_no_solution(self):
        a = pf.AStar()
        walls = ((0, 5), (1, 0), (1, 1), (1, 2), (1, 3), (1, 4), (1, 5),
                 (2, 3), (3, 1), (3, 2), (3, 5), (4, 1), (4, 4), (5, 1))
        a.init_grid(6, 6, walls, (0, 0), (5, 5))
        self.assertIsNone(a.solve())

if __name__ == '__main__':
    unittest.main()