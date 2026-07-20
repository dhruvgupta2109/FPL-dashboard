class Solution(object):
    def uniqueXorTriplets(self, nums):
        """
        :type nums: List[int]
        :rtype: int
        """
        un = list(set(nums))
        mv = max(un) if un else 0
        l = 1 << (mv.bit_length())

        has = [False] * l
        for x in un:
            has[x] = True

        cp = [False] * l
        for i in range(len(un)):
            for j in range(i, len(un)):
                cp[un[i] ^ un[j]] = True

        ct = [False] * l
        for x in range(l):
            if cp[x]:
                for y in un:
                    ct[x ^ y] = True

        return sum(ct)
