class FeedbackAgent:
    def __init__(self, min_length=10, max_retries=2):
        self.min_length = min_length
        self.max_retries = max_retries

    def check_and_improve(self, output: str, original_input: str, agent):
        retries = 0
        improved_output = output

        # 리스트나 튜플인 경우 처리
        if isinstance(improved_output, (list, tuple)):
            if improved_output:
                if isinstance(improved_output, tuple):
                    # 튜플의 첫 번째 항목이 문자열인 경우 사용
                    improved_output = (
                        improved_output[0] if isinstance(improved_output[0], str) else str(improved_output[0])
                    )
                else:  # 리스트인 경우
                    improved_output = improved_output[0]
            else:
                improved_output = ""

        # 문자열이 아닌 경우 문자열로 변환
        if not isinstance(improved_output, str):
            improved_output = str(improved_output)

        while len(improved_output.strip()) < self.min_length and retries < self.max_retries:
            improved_input = original_input + "\n추가 상세 설명 부탁해."
            new_output = agent.run(improved_input)

            # 리스트나 튜플인 경우 처리
            if isinstance(new_output, (list, tuple)):
                if new_output:
                    if isinstance(new_output, tuple):
                        # 튜플의 첫 번째 항목이 문자열인 경우 사용
                        new_output = new_output[0] if isinstance(new_output[0], str) else str(new_output[0])
                    else:  # 리스트인 경우
                        new_output = new_output[0]
                else:
                    break

            # 문자열이 아닌 경우 문자열로 변환
            if not isinstance(new_output, str):
                new_output = str(new_output)

            improved_output = new_output
            retries += 1

        return improved_output
