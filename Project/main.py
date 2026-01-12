import imgui
import glfw
import OpenGL.GL as gl
import read_data
import calc_plan
import enums
import threading
import optimize_sol
from imgui.integrations.glfw import GlfwRenderer
from array import array
from optimize_sol import opt_instance
from tkinter import Tk
from tkinter.filedialog import askdirectory


def impl_glfw_init(window_name="Planowanie zajęć AGH", width=1280, height=720):
    if not glfw.init():
        print("Could not initialize OpenGL context")
        exit(1)

    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
    glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)

    glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, gl.GL_TRUE)

    # Create a windowed mode window and its OpenGL context
    window = glfw.create_window(int(width), int(height), window_name, None, None)
    glfw.make_context_current(window)

    if not window:
        glfw.terminate()
        print("Could not initialize Window")
        exit(1)

    return window


class GUI(object):

    instance = None

    def __init__(self):
        super().__init__()

        if GUI.instance is None:
            GUI.instance = self

        self.backgroundColor = (0, 0, 0, 1)
        self.window = impl_glfw_init()
        gl.glClearColor(*self.backgroundColor)
        imgui.create_context()
        self.impl = GlfwRenderer(self.window)

        self.data_folder = r"data"
        self.best_val = 0

        style = imgui.get_style()
        style.colors[imgui.COLOR_BUTTON] = [0.26/2, 0.59/2, 0.98/2, 1.0]


        self.opt_step = False
        self.show_preview = False
        self.is_running = False
        self.plan = None
        self.algorytm_thread = None

        io = imgui.get_io()
        self.font = io.fonts.add_font_from_file_ttf("font.ttf", 20, None, io.fonts.get_glyph_ranges_latin())
        self.impl.refresh_font_texture()

        self.loop()

    def print_params(self):
        if imgui.collapsing_header("Parametry", None)[0]:
            _, opt_instance.start_T = imgui.input_float('Temperatura', opt_instance.start_T)
            _, opt_instance.alpha = imgui.input_float('Współczynnik chłodzienia', opt_instance.alpha)
            _, opt_instance.max_iter = imgui.input_int('Maksymalna liczba iteracji', opt_instance.max_iter)

        return

    def loop(self):
        while not glfw.window_should_close(self.window):
            glfw.poll_events()
            self.impl.process_inputs()
            imgui.new_frame()
            imgui.push_font(self.font)

            io = imgui.get_io()
            display_w, display_h = io.display_size

            imgui.set_next_window_position(0,0)
            imgui.set_next_window_size(display_w, display_h)
            imgui.begin("Custom window", 
                flags=(
                    imgui.WINDOW_NO_TITLE_BAR |
                    imgui.WINDOW_NO_RESIZE |
                    imgui.WINDOW_NO_MOVE |
                    imgui.WINDOW_NO_BACKGROUND
                )
            )

            imgui.text("Data Folder")
            imgui.same_line()   
            _, self.data_folder = imgui.input_text("", self.data_folder)
            imgui.same_line()
            if imgui.button("Zmień"):
                path = askdirectory(title="Wybierz Folder")
                if path is not None and path != "":
                    self.data_folder = path

                    calc_plan.invalidate_data()
                    read_data.set_data_folder = self.data_folder

            imgui.separator()


            if not self.is_running:
                self.print_params()
                if imgui.button("Oblicz plan"):
                    self.category = 0
                    self.current_select = 0
                    self.plan = calc_plan.prepare_plan()

                    self.is_running = True
                    opt_instance.setup(self.plan, calc_plan.get_data())

                    if not self.show_preview:
                        self.opt_step = False

                    if self.show_preview:
                        self.calc_plan_for_student()
                    else:
                        t = threading.Thread(target=opt_instance.run, daemon=True)
                        self.algorytm_thread = t
                        t.start()

                imgui.same_line()
                _, self.show_preview = imgui.checkbox("Podgląd", self.show_preview)
                if self.show_preview:
                    imgui.same_line()
                    _, self.opt_step = imgui.checkbox("Krok po kroku", self.opt_step)
            elif self.algorytm_thread is not None:
                imgui.text("Algorytm działa...")

            elif self.show_preview:
                if not self.opt_step or imgui.button("Krok"):
                    should_continue, self.plan = opt_instance.step()
                    self.calc_plan_for_student()
                    if not should_continue:
                        self.is_running = False
                imgui.same_line()
                if imgui.button("Zakończ"):
                    self.is_running = False

            if (self.algorytm_thread is not None or self.show_preview) and self.is_running:
                imgui.label_text("##2", f"Temperatura: {opt_instance.T}")
                self.best_val, _ = optimize_sol.goal_function(self.plan, calc_plan.get_data())
                imgui.label_text("##1", f"Wartość funkcji celu: {self.best_val}")
                    
            if self.is_running and self.algorytm_thread is not None and not self.algorytm_thread.is_alive():
                self.is_running = False
                self.algorytm_thread = None
                self.plan = opt_instance.get_result()
                self.best_val, _ = optimize_sol.goal_function(self.plan, calc_plan.get_data())

                self.calc_plan_for_student()
            

            if self.plan is not None:
                _, new_select = imgui.combo("Category", self.category, ["Wszystko", "Studenci", "Prowadzący", "Sale"])
                if new_select != self.category:
                    self.category = new_select
                    self.current_select = 0
                    self.calc_plan_for_student()

                if not self.is_running:
                    imgui.label_text("##1", f"Finalna wartość funkcji celu: {self.best_val}")

                    if imgui.collapsing_header("Wykres", None)[0]:
                        values = array('f', opt_instance.goal_log)
                        imgui.plot_lines(label="Funckja celu", values=values, graph_size=(0,100))



            if self.plan is not None and self.category != 0:
                cur_array = []
                new_select = self.current_select
                if self.category == 1:
                    cur_array = list(calc_plan.get_data()[enums.DataEnum.STUDENT_DICT].keys())
                    _, new_select = imgui.combo("##students", self.current_select, cur_array)
                elif self.category == 2:
                    cur_array = list(calc_plan.get_data()[enums.DataEnum.LECTURER_DICT].keys())
                    _, new_select = imgui.combo("##lecturers", self.current_select, cur_array)
                elif self.category == 3:
                    cur_array = list(calc_plan.get_data()[enums.DataEnum.ROOM_GROUPS].keys())
                    _, new_select = imgui.combo("##rooms", self.current_select, cur_array)

                if new_select != self.current_select:
                    self.current_select = new_select
                    self.calc_plan_for_student()



            if self.plan is not None and self.algorytm_thread is None:
                # if self.unassigned_groups is not None and len(self.unassigned_groups) > 0:
                #     text = "Nieprzydzielone grupy: "
                #     text = text + ', '.join(self.unassigned_groups)
                #     imgui.text(text)
                self.render_grid()
                    
            imgui.pop_font()

            imgui.end()

            imgui.render()

            gl.glClearColor(*self.backgroundColor)
            gl.glClear(gl.GL_COLOR_BUFFER_BIT)

            self.impl.render(imgui.get_draw_data())
            glfw.swap_buffers(self.window)

        self.impl.shutdown()
        glfw.terminate()

    def get_max_concurrent(self, subjects):
        return optimize_sol.get_max_concurrent(calc_plan.get_data(), subjects)

    def get_subject_list(self):
        data = calc_plan.get_data()
        students = data[enums.DataEnum.STUDENT_DICT];
        lecturers = data[enums.DataEnum.LECTURER_DICT]
        rooms = data[enums.DataEnum.ROOM_GROUPS]

        if self.category == 0:
            return list(data[enums.DataEnum.SUBJECT_DICT].keys())
        elif self.category == 1:
            return students[list(students.keys())[self.current_select ]]
        elif self.category == 2:
            return lecturers[list(lecturers.keys())[self.current_select]]
        elif self.category == 3:
            return rooms[list(rooms.keys())[self.current_select]]
        return []

    def calc_plan_for_student(self):
        # dla testów
        self.best_val, _ = optimize_sol.goal_function(self.plan, calc_plan.get_data())
        self.columns_per_day = [1,1,1,1,1]
        data = calc_plan.get_data()
        students = data[enums.DataEnum.STUDENT_DICT];
        subs = self.get_subject_list()
        for i in range(5):
            subjects = [(k,v[0]) for k,v in self.plan.items() if v[1] == i and k in subs]
            cols = self.get_max_concurrent(subjects)
            self.columns_per_day[i] = cols
            if self.columns_per_day[i] <= 0:
                self.columns_per_day[i] = 1
        
        self.total_cols = sum(self.columns_per_day)


    def render_grid(self):
        if self.total_cols == 0:
            return

        draw_list = imgui.get_window_draw_list()
        right_padding = 100

        data = calc_plan.get_data()
        io = imgui.get_io()
        display_w, display_h = io.display_size
        display_w -= 50 + right_padding

        pos_x, pos_y = imgui.get_cursor_pos()
        pos_x += right_padding

        size_x = display_w / self.total_cols
        subject_data = data[enums.DataEnum.SUBJECT_DICT];
        subs = self.get_subject_list()
        text_pos_y = pos_y

        dni = ["Poniedziałek", "Wtorek", "Środa", "Czwartek", "Piątek"]
        for i in range(5):
            offset_x = sum(self.columns_per_day[0:i])
            column_size = size_x * (self.columns_per_day[i])
            text_size_x, _ = imgui.calc_text_size(dni[i])
            imgui.set_cursor_pos([pos_x + ((column_size-text_size_x)/2) + (offset_x * size_x), pos_y])
            imgui.text(dni[i])

        button_padding = 10

        pos_x, pos_y = imgui.get_cursor_pos()
        pos_y += 10
        pos_x += right_padding
        lowest_point = (2000 - 800) 

        for i in range((int)((2100-800)/100)):
            time = (8*60) + i * 60
            draw_list.add_line(0,
                                pos_y + 60*i,
                                display_w + right_padding + button_padding,
                                pos_y + 60*i,
                                imgui.get_color_u32_rgba(0.5, 0.5, 0.5, 0.5))

            cur_cur = imgui.get_cursor_pos()
            imgui.set_cursor_pos([pos_x - right_padding, pos_y + 60*i + 7])
            imgui.text(f"{time // 60:02d}:00")

            imgui.set_cursor_pos(cur_cur)

        lecturers = data[enums.DataEnum.LECTURER_DICT]
        rooms = data[enums.DataEnum.ROOM_GROUPS]
        for i in range(5):
            latest_end = [-1] * self.columns_per_day[i]
            subjects = [(k,v[0]) for k,v in self.plan.items() if v[1] == i and k in subs]
            subjects.sort(key=lambda x: x[1])
            for s in subjects:
                x_index = 0
                duration = subject_data[s[0]][0]
                start = s[1]
                end = start + duration

                while latest_end[x_index] > start:
                    x_index += 1

                if x_index > self.columns_per_day[i]:
                    return
                    
                current_x = pos_x + (sum(self.columns_per_day[0:i])+x_index)*size_x
                imgui.set_cursor_position([current_x + (button_padding / 2), pos_y + s[1] + (button_padding/2)])

                lecturer = ""
                room = ""
                for k,v in lecturers.items():
                    if s[0] in v:
                        lecturer = k
                        break
                for k,v in rooms.items():
                    if s[0] in v:
                        room = k
                        break

                text = s[0] + "\n" + lecturer + "\n" + room
                imgui.button(text, size_x - button_padding, subject_data[s[0]][0] - button_padding)
                latest_end[x_index] = end

        for i in range(5):
            offset_x = sum(self.columns_per_day[0:i])
            offset_x = size_x * (self.columns_per_day[i] + offset_x)
            offset_x += pos_x

            if i == 4:
                offset_x = pos_x

            draw_list.add_line(offset_x, text_pos_y, offset_x, lowest_point, imgui.get_color_u32_rgba(0.5, 0.5, 0.5, 0.5))

if __name__ == "__main__":
    gui = GUI()

